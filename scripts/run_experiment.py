#!/usr/bin/env python3
"""
Experiment Simulation Script

Simulates control vs experimental group comparison for research evaluation.
"""
import argparse
import json
import csv
import random
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlmodel import Session, SQLModel, create_engine
from app.db.models import Student, Question, Attempt, BaselineLevel, QuestionType, DifficultyLevel
from app.db.concept_graph import CONCEPT_GRAPH, MISCONCEPTIONS, get_recommended_order
from app.metrics.research import compute_all_metrics


def create_synthetic_student(
    session: Session,
    username: str,
    baseline: str,
    is_control: bool
) -> Student:
    """Create a synthetic student."""
    import hashlib
    
    student = Student(
        username=username,
        password_hash=hashlib.sha256(b"test123").hexdigest(),
        baseline_level=BaselineLevel(baseline),
        is_control_group=is_control,
        mastery_scores={},
        pretest_completed=True,
        posttest_completed=False,
        current_concept="variables"
    )
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


def simulate_pretest(
    session: Session,
    student: Student,
    questions: List[Question]
) -> Dict:
    """Simulate pretest performance based on baseline level."""
    # Performance probability by baseline
    prob = {"low": 0.3, "medium": 0.5, "high": 0.7}
    base_prob = prob.get(student.baseline_level.value, 0.5)
    
    correct = 0
    total = 0
    
    for q in questions:
        if not q.is_pretest:
            continue
        
        # Adjust probability by difficulty
        diff_adjust = {"easy": 0.2, "medium": 0.0, "hard": -0.2}
        p = base_prob + diff_adjust.get(q.difficulty.value, 0)
        
        is_correct = random.random() < p
        if is_correct:
            correct += 1
        total += 1
        
        # Determine misconceptions
        misconceptions = []
        if not is_correct:
            concept_miscs = CONCEPT_GRAPH.get(q.concept)
            if concept_miscs and concept_miscs.misconceptions:
                misconceptions = random.sample(
                    concept_miscs.misconceptions,
                    min(2, len(concept_miscs.misconceptions))
                )
        
        attempt = Attempt(
            student_id=student.id,
            question_id=q.id,
            response="A" if is_correct else "B",  # Simplified
            is_correct=is_correct,
            misconceptions=misconceptions,
            confidence_score=random.uniform(0.5, 0.9),
            submitted_at=datetime.utcnow() - timedelta(days=7)
        )
        session.add(attempt)
        
        # Update mastery
        current = student.mastery_scores.get(q.concept, 0.5)
        student.mastery_scores[q.concept] = current * 0.8 + (1.0 if is_correct else 0.0) * 0.2
    
    session.add(student)
    session.commit()
    
    return {"correct": correct, "total": total, "score": correct / max(total, 1)}


def simulate_learning_control(
    session: Session,
    student: Student,
    questions: List[Question],
    iterations: int = 20
) -> Dict:
    """Simulate learning for control group (static quizzes only)."""
    # Control group: random questions, no adaptation
    adaptive_questions = [q for q in questions if not q.is_pretest and not q.is_posttest]
    
    correct = 0
    total = 0
    
    for _ in range(iterations):
        if not adaptive_questions:
            break
        
        q = random.choice(adaptive_questions)
        
        # Small improvement over time (10% boost from practice)
        base_prob = {"low": 0.35, "medium": 0.55, "high": 0.75}
        p = base_prob.get(student.baseline_level.value, 0.5)
        is_correct = random.random() < p
        
        if is_correct:
            correct += 1
        total += 1
        
        misconceptions = []
        if not is_correct:
            possible = list(MISCONCEPTIONS.keys())[:5]
            misconceptions = random.sample(possible, min(1, len(possible)))
        
        attempt = Attempt(
            student_id=student.id,
            question_id=q.id,
            response="A" if is_correct else "C",
            is_correct=is_correct,
            misconceptions=misconceptions,
            confidence_score=random.uniform(0.4, 0.8),
            submitted_at=datetime.utcnow() - timedelta(days=random.randint(1, 6))
        )
        session.add(attempt)
        
        # Slow improvement for control
        current = student.mastery_scores.get(q.concept, 0.5)
        student.mastery_scores[q.concept] = min(1.0, current * 0.95 + (1.0 if is_correct else 0.0) * 0.05)
    
    session.add(student)
    session.commit()
    
    return {"correct": correct, "total": total}


def simulate_learning_experimental(
    session: Session,
    student: Student,
    questions: List[Question],
    iterations: int = 20
) -> Dict:
    """Simulate learning for experimental group (adaptive agentic loop)."""
    # Experimental: adaptive questions with remediation
    adaptive_questions = [q for q in questions if not q.is_pretest and not q.is_posttest]
    
    correct = 0
    total = 0
    consecutive_correct = 0
    
    # Track concept focus based on weakness
    concepts = get_recommended_order()
    current_concept_idx = 0
    
    for i in range(iterations):
        if not adaptive_questions:
            break
        
        # Adaptive: focus on weak concepts
        weak_concepts = [
            c for c in concepts 
            if student.mastery_scores.get(c, 0.5) < 0.7
        ]
        
        if weak_concepts:
            target_concept = weak_concepts[0]
        else:
            # All strong - review
            target_concept = concepts[i % len(concepts)]
        
        # Find question for target concept
        concept_questions = [q for q in adaptive_questions if q.concept == target_concept]
        q = random.choice(concept_questions) if concept_questions else random.choice(adaptive_questions)
        
        # Higher improvement due to adaptation + teaching
        base_prob = {"low": 0.45, "medium": 0.65, "high": 0.85}
        p = base_prob.get(student.baseline_level.value, 0.6)
        
        # Boost from consecutive correct (momentum)
        p += min(consecutive_correct * 0.05, 0.15)
        p = min(p, 0.95)
        
        is_correct = random.random() < p
        
        if is_correct:
            correct += 1
            consecutive_correct += 1
        else:
            consecutive_correct = 0
        total += 1
        
        misconceptions = []
        if not is_correct:
            concept = CONCEPT_GRAPH.get(q.concept)
            if concept and concept.misconceptions:
                misconceptions = random.sample(
                    concept.misconceptions,
                    min(1, len(concept.misconceptions))
                )
        
        attempt = Attempt(
            student_id=student.id,
            question_id=q.id,
            response="A" if is_correct else "B",
            is_correct=is_correct,
            misconceptions=misconceptions,
            confidence_score=random.uniform(0.6, 0.95),
            submitted_at=datetime.utcnow() - timedelta(days=random.randint(1, 6))
        )
        session.add(attempt)
        
        # Faster improvement for experimental (adaptive benefit)
        current = student.mastery_scores.get(q.concept, 0.5)
        if is_correct:
            student.mastery_scores[q.concept] = min(1.0, current * 0.85 + 0.15)
        else:
            # Still learn from mistakes (remediation effect)
            student.mastery_scores[q.concept] = min(1.0, current * 0.92 + 0.03)
    
    session.add(student)
    session.commit()
    
    return {"correct": correct, "total": total}


def simulate_posttest(
    session: Session,
    student: Student,
    questions: List[Question]
) -> Dict:
    """Simulate posttest performance."""
    correct = 0
    total = 0
    
    for q in questions:
        if not q.is_posttest:
            continue
        
        # Use current mastery
        concept_mastery = student.mastery_scores.get(q.concept, 0.5)
        
        # Difficulty adjustment
        diff_adjust = {"easy": 0.1, "medium": 0.0, "hard": -0.1}
        p = concept_mastery + diff_adjust.get(q.difficulty.value, 0)
        p = max(0.1, min(0.95, p))
        
        is_correct = random.random() < p
        if is_correct:
            correct += 1
        total += 1
        
        attempt = Attempt(
            student_id=student.id,
            question_id=q.id,
            response="A" if is_correct else "D",
            is_correct=is_correct,
            misconceptions=[],
            confidence_score=concept_mastery,
            submitted_at=datetime.utcnow()
        )
        session.add(attempt)
    
    student.posttest_completed = True
    session.add(student)
    session.commit()
    
    return {"correct": correct, "total": total, "score": correct / max(total, 1)}


def run_experiment(
    control_size: int = 50,
    experimental_size: int = 50,
    iterations: int = 20,
    output_dir: str = "data/exports"
):
    """Run the full experiment simulation."""
    print(f"\n{'='*60}")
    print("AGENTIC COPILOT EXPERIMENT SIMULATION")
    print(f"{'='*60}\n")
    
    # Create in-memory database for simulation
    engine = create_engine("sqlite:///./data/experiment.db", echo=False)
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # Load seed questions
        seed_path = "data/seed/questions.json"
        if os.path.exists(seed_path):
            with open(seed_path, "r") as f:
                seed_data = json.load(f)
            
            for q in seed_data.get("mcq_questions", []):
                question = Question(
                    question_type=QuestionType.MCQ,
                    difficulty=DifficultyLevel(q.get("difficulty", "medium")),
                    concept=q.get("concept", "variables"),
                    prompt=q.get("prompt", ""),
                    options=q.get("options", {}),
                    correct_answer=q.get("correct_answer", ""),
                    is_pretest=q.get("is_pretest", False),
                    is_posttest=q.get("is_posttest", False)
                )
                session.add(question)
            
            for q in seed_data.get("coding_questions", []):
                question = Question(
                    question_type=QuestionType.CODING,
                    difficulty=DifficultyLevel(q.get("difficulty", "medium")),
                    concept=q.get("concept", "variables"),
                    prompt=q.get("prompt", ""),
                    starter_code=q.get("starter_code", ""),
                    test_cases=q.get("test_cases", {}),
                    solution=q.get("solution", "")
                )
                session.add(question)
            
            session.commit()
        
        questions = list(session.exec(SQLModel.select(Question)).all())
        print(f"Loaded {len(questions)} questions")
        
        # Create students
        control_students = []
        experimental_students = []
        
        baselines = ["low", "medium", "high"]
        
        print(f"\nCreating {control_size} control + {experimental_size} experimental students...")
        
        for i in range(control_size):
            baseline = baselines[i % 3]
            s = create_synthetic_student(session, f"control_{i+1}", baseline, True)
            control_students.append(s)
        
        for i in range(experimental_size):
            baseline = baselines[i % 3]
            s = create_synthetic_student(session, f"experimental_{i+1}", baseline, False)
            experimental_students.append(s)
        
        print(f"Created {len(control_students)} control, {len(experimental_students)} experimental")
        
        # Run pretest
        print("\n--- PRETEST PHASE ---")
        control_pre = []
        exp_pre = []
        
        for s in control_students:
            result = simulate_pretest(session, s, questions)
            control_pre.append(result["score"])
        
        for s in experimental_students:
            result = simulate_pretest(session, s, questions)
            exp_pre.append(result["score"])
        
        print(f"Control pretest avg: {sum(control_pre)/len(control_pre):.2%}")
        print(f"Experimental pretest avg: {sum(exp_pre)/len(exp_pre):.2%}")
        
        # Run learning phase
        print(f"\n--- LEARNING PHASE ({iterations} iterations) ---")
        
        for s in control_students:
            simulate_learning_control(session, s, questions, iterations)
        print(f"Control group completed learning (static quizzes)")
        
        for s in experimental_students:
            simulate_learning_experimental(session, s, questions, iterations)
        print(f"Experimental group completed learning (adaptive agentic)")
        
        # Run posttest
        print("\n--- POSTTEST PHASE ---")
        control_post = []
        exp_post = []
        
        for s in control_students:
            session.refresh(s)
            result = simulate_posttest(session, s, questions)
            control_post.append(result["score"])
        
        for s in experimental_students:
            session.refresh(s)
            result = simulate_posttest(session, s, questions)
            exp_post.append(result["score"])
        
        print(f"Control posttest avg: {sum(control_post)/len(control_post):.2%}")
        print(f"Experimental posttest avg: {sum(exp_post)/len(exp_post):.2%}")
        
        # Compute metrics
        print("\n--- COMPUTING METRICS ---")
        metrics = compute_all_metrics(session)
        
        # Calculate comparison
        control_improvement = sum(control_post) / len(control_post) - sum(control_pre) / len(control_pre)
        exp_improvement = sum(exp_post) / len(exp_post) - sum(exp_pre) / len(exp_pre)
        
        # Save results
        os.makedirs(output_dir, exist_ok=True)
        
        results = {
            "experiment_date": datetime.now().isoformat(),
            "control_size": control_size,
            "experimental_size": experimental_size,
            "iterations": iterations,
            "control": {
                "pretest_avg": sum(control_pre) / len(control_pre),
                "posttest_avg": sum(control_post) / len(control_post),
                "improvement": control_improvement
            },
            "experimental": {
                "pretest_avg": sum(exp_pre) / len(exp_pre),
                "posttest_avg": sum(exp_post) / len(exp_post),
                "improvement": exp_improvement
            },
            "advantage": {
                "improvement_delta": exp_improvement - control_improvement,
                "posttest_delta": sum(exp_post)/len(exp_post) - sum(control_post)/len(control_post)
            },
            "metrics": metrics
        }
        
        with open(os.path.join(output_dir, "experiment_results.json"), "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        # Export CSV logs
        with open(os.path.join(output_dir, "experiment_logs.csv"), "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["student_id", "group", "baseline", "pretest", "posttest", "improvement"])
            
            for i, s in enumerate(control_students):
                writer.writerow([
                    s.id, "control", s.baseline_level.value,
                    control_pre[i], control_post[i],
                    control_post[i] - control_pre[i]
                ])
            
            for i, s in enumerate(experimental_students):
                writer.writerow([
                    s.id, "experimental", s.baseline_level.value,
                    exp_pre[i], exp_post[i],
                    exp_post[i] - exp_pre[i]
                ])
        
        # Print summary
        print(f"\n{'='*60}")
        print("EXPERIMENT RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"\nControl Group (n={control_size}):")
        print(f"  Pretest:  {sum(control_pre)/len(control_pre):.1%}")
        print(f"  Posttest: {sum(control_post)/len(control_post):.1%}")
        print(f"  Improvement: {control_improvement:.1%}")
        
        print(f"\nExperimental Group (n={experimental_size}):")
        print(f"  Pretest:  {sum(exp_pre)/len(exp_pre):.1%}")
        print(f"  Posttest: {sum(exp_post)/len(exp_post):.1%}")
        print(f"  Improvement: {exp_improvement:.1%}")
        
        print(f"\nADVANTAGE OF AGENTIC COPILOT:")
        print(f"  Additional improvement: {(exp_improvement - control_improvement):.1%}")
        print(f"  Effect size (Cohen's d): {metrics['pre_post_comparison'].get('cohens_d', 'N/A')}")
        
        print(f"\nResults saved to:")
        print(f"  - {output_dir}/experiment_results.json")
        print(f"  - {output_dir}/experiment_logs.csv")
        print(f"{'='*60}\n")
        
        return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run experiment simulation")
    parser.add_argument("--control", type=int, default=50, help="Control group size")
    parser.add_argument("--experimental", type=int, default=50, help="Experimental group size")
    parser.add_argument("--iterations", type=int, default=20, help="Learning iterations per student")
    parser.add_argument("--output", type=str, default="data/exports", help="Output directory")
    
    args = parser.parse_args()
    
    run_experiment(
        control_size=args.control,
        experimental_size=args.experimental,
        iterations=args.iterations,
        output_dir=args.output
    )
