"""
Research Metrics Computation

Computes statistical metrics for research evaluation.
"""
import json
from typing import Dict, List, Tuple
from collections import defaultdict
import math

from sqlmodel import Session, select
from app.db import Student, Attempt, Question


def compute_all_metrics(session: Session) -> Dict:
    """Compute all research metrics."""
    students = session.exec(select(Student)).all()
    attempts = session.exec(select(Attempt)).all()
    questions = session.exec(select(Question)).all()
    
    return {
        "item_analysis": compute_item_analysis(attempts, questions),
        "pre_post_comparison": compute_pre_post(session, students),
        "diagnostic_accuracy": compute_diagnostic_accuracy(session),
        "equity_analysis": compute_equity_analysis(students),
        "summary_stats": compute_summary_stats(students, attempts)
    }


def compute_item_analysis(attempts: List[Attempt], questions: List[Question]) -> Dict:
    """Compute item difficulty (p-value) and discrimination index."""
    results = {}
    
    # Group attempts by question
    question_attempts = defaultdict(list)
    for a in attempts:
        question_attempts[a.question_id].append(a)
    
    for q in questions:
        q_attempts = question_attempts.get(q.id, [])
        if not q_attempts:
            continue
        
        # P-value (difficulty) = proportion correct
        correct = sum(1 for a in q_attempts if a.is_correct)
        total = len(q_attempts)
        p_value = correct / total if total > 0 else 0
        
        # Discrimination index (simplified point-biserial)
        # Compare high performers vs low performers
        student_totals = defaultdict(lambda: {"correct": 0, "total": 0})
        for a in attempts:
            student_totals[a.student_id]["total"] += 1
            if a.is_correct:
                student_totals[a.student_id]["correct"] += 1
        
        student_scores = [
            (sid, d["correct"] / d["total"] if d["total"] > 0 else 0)
            for sid, d in student_totals.items()
        ]
        student_scores.sort(key=lambda x: x[1], reverse=True)
        
        n = len(student_scores)
        if n >= 4:
            top_27 = set(s[0] for s in student_scores[:max(int(n * 0.27), 1)])
            bottom_27 = set(s[0] for s in student_scores[-max(int(n * 0.27), 1):])
            
            top_correct = sum(1 for a in q_attempts if a.student_id in top_27 and a.is_correct)
            top_total = sum(1 for a in q_attempts if a.student_id in top_27)
            
            bottom_correct = sum(1 for a in q_attempts if a.student_id in bottom_27 and a.is_correct)
            bottom_total = sum(1 for a in q_attempts if a.student_id in bottom_27)
            
            top_p = top_correct / top_total if top_total > 0 else 0
            bottom_p = bottom_correct / bottom_total if bottom_total > 0 else 0
            discrimination = top_p - bottom_p
        else:
            discrimination = 0
        
        results[q.id] = {
            "question_id": q.id,
            "concept": q.concept,
            "p_value": round(p_value, 3),
            "difficulty": "easy" if p_value > 0.7 else ("hard" if p_value < 0.3 else "medium"),
            "discrimination": round(discrimination, 3),
            "n_attempts": total
        }
    
    return results


def compute_pre_post(session: Session, students: List[Student]) -> Dict:
    """Compute pre-post improvement and Cohen's d."""
    pre_scores = []
    post_scores = []
    
    for student in students:
        if not student.pretest_completed or not student.posttest_completed:
            continue
        
        # Get pretest attempts
        pre_attempts = session.exec(
            select(Attempt)
            .join(Question)
            .where(Attempt.student_id == student.id)
            .where(Question.is_pretest == True)
        ).all()
        
        # Get posttest attempts
        post_attempts = session.exec(
            select(Attempt)
            .join(Question)
            .where(Attempt.student_id == student.id)
            .where(Question.is_posttest == True)
        ).all()
        
        if pre_attempts and post_attempts:
            pre_score = sum(1 for a in pre_attempts if a.is_correct) / len(pre_attempts)
            post_score = sum(1 for a in post_attempts if a.is_correct) / len(post_attempts)
            pre_scores.append(pre_score)
            post_scores.append(post_score)
    
    if not pre_scores or not post_scores:
        return {
            "n_students": 0,
            "pre_mean": 0,
            "post_mean": 0,
            "improvement": 0,
            "cohens_d": 0,
            "effect_size": "none"
        }
    
    pre_mean = sum(pre_scores) / len(pre_scores)
    post_mean = sum(post_scores) / len(post_scores)
    improvement = post_mean - pre_mean
    
    # Cohen's d
    pooled_std = math.sqrt(
        (sum((x - pre_mean) ** 2 for x in pre_scores) + 
         sum((x - post_mean) ** 2 for x in post_scores)) / 
        (len(pre_scores) + len(post_scores) - 2)
    ) if len(pre_scores) > 1 else 1
    
    cohens_d = improvement / pooled_std if pooled_std > 0 else 0
    
    # Interpret effect size
    if abs(cohens_d) < 0.2:
        effect = "negligible"
    elif abs(cohens_d) < 0.5:
        effect = "small"
    elif abs(cohens_d) < 0.8:
        effect = "medium"
    else:
        effect = "large"
    
    return {
        "n_students": len(pre_scores),
        "pre_mean": round(pre_mean, 3),
        "post_mean": round(post_mean, 3),
        "improvement": round(improvement, 3),
        "improvement_pct": round(improvement * 100, 1),
        "cohens_d": round(cohens_d, 3),
        "effect_size": effect
    }


def compute_diagnostic_accuracy(session: Session) -> Dict:
    """Compute diagnostic precision, recall, and Cohen's kappa vs expert labels."""
    import os
    
    # Load expert labels
    expert_path = "data/seed/expert_labels.json"
    if not os.path.exists(expert_path):
        return {"error": "Expert labels not found", "precision": 0, "recall": 0, "kappa": 0}
    
    with open(expert_path, "r") as f:
        expert_data = json.load(f)
    
    expert_labels = expert_data.get("labels", [])
    
    # Build lookup for expert labels
    expert_lookup = {}
    for label in expert_labels:
        key = (label["question_id"], label["student_response"])
        expert_lookup[key] = set(label["expert_misconceptions"])
    
    # Get system predictions
    attempts = session.exec(select(Attempt)).all()
    
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    
    for attempt in attempts:
        key = (attempt.question_id, attempt.response)
        if key not in expert_lookup:
            continue
        
        expert_miscs = expert_lookup[key]
        predicted_miscs = set(attempt.misconceptions or [])
        
        # Calculate matches
        tp = len(expert_miscs & predicted_miscs)
        fp = len(predicted_miscs - expert_miscs)
        fn = len(expert_miscs - predicted_miscs)
        
        true_positives += tp
        false_positives += fp
        false_negatives += fn
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    # Simplified Cohen's kappa (treating as binary agreement)
    # Po = observed agreement, Pe = expected agreement
    total = true_positives + false_positives + false_negatives
    po = true_positives / total if total > 0 else 0
    pe = 0.5  # Random chance for binary
    kappa = (po - pe) / (1 - pe) if (1 - pe) > 0 else 0
    
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "cohens_kappa": round(kappa, 3),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives
    }


def compute_equity_analysis(students: List[Student]) -> Dict:
    """Analyze equity across baseline levels."""
    groups = {"low": [], "medium": [], "high": []}
    
    for student in students:
        level = student.baseline_level.value if student.baseline_level else "medium"
        mastery = student.mastery_scores or {}
        if mastery:
            avg = sum(mastery.values()) / len(mastery)
            groups[level].append(avg)
    
    results = {}
    for level, scores in groups.items():
        if scores:
            results[level] = {
                "n_students": len(scores),
                "mean_mastery": round(sum(scores) / len(scores), 3),
                "min_mastery": round(min(scores), 3),
                "max_mastery": round(max(scores), 3)
            }
        else:
            results[level] = {"n_students": 0, "mean_mastery": 0}
    
    # Check for equity gap
    means = [r["mean_mastery"] for r in results.values() if r["n_students"] > 0]
    if len(means) >= 2:
        gap = max(means) - min(means)
        equity_status = "good" if gap < 0.1 else ("moderate" if gap < 0.2 else "concerning")
    else:
        gap = 0
        equity_status = "insufficient_data"
    
    results["equity_gap"] = round(gap, 3)
    results["equity_status"] = equity_status
    
    return results


def compute_summary_stats(students: List[Student], attempts: List[Attempt]) -> Dict:
    """Compute summary statistics."""
    total_students = len(students)
    total_attempts = len(attempts)
    correct_attempts = sum(1 for a in attempts if a.is_correct)
    
    # Average mastery
    all_mastery = []
    for s in students:
        if s.mastery_scores:
            all_mastery.extend(s.mastery_scores.values())
    
    return {
        "total_students": total_students,
        "students_completed_pretest": sum(1 for s in students if s.pretest_completed),
        "students_completed_posttest": sum(1 for s in students if s.posttest_completed),
        "total_attempts": total_attempts,
        "overall_accuracy": round(correct_attempts / total_attempts, 3) if total_attempts > 0 else 0,
        "average_mastery": round(sum(all_mastery) / len(all_mastery), 3) if all_mastery else 0,
        "control_group_size": sum(1 for s in students if s.is_control_group),
        "experimental_group_size": sum(1 for s in students if not s.is_control_group)
    }
