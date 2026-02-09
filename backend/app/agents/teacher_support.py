"""
Teacher Support Agent

Provides analytics and intervention suggestions for instructors.
"""
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import Counter

from sqlmodel import Session, select
from app.db.models import Student, Attempt, Question
from app.db.concept_graph import MISCONCEPTIONS, CONCEPT_GRAPH
from app.llm import get_llm_provider


@dataclass
class StudentCluster:
    """A cluster of students with similar issues."""
    misconception: str
    students: List[int]
    severity: str
    recommended_intervention: str


@dataclass 
class InstructorAnalytics:
    """Analytics for instructor dashboard."""
    total_students: int
    struggling_students: List[int]
    concept_heatmap: Dict[str, Dict[str, int]]  # concept -> {struggling, developing, mastered}
    misconception_clusters: List[StudentCluster]
    priority_students: List[Dict]
    intervention_suggestions: List[str]


class TeacherSupportAgent:
    """Provides instructor-facing analytics and suggestions."""
    
    def __init__(self, session: Session):
        self.session = session
        self.llm = get_llm_provider()
    
    def get_analytics(self) -> InstructorAnalytics:
        """Generate comprehensive instructor analytics."""
        students = self.session.exec(select(Student)).all()
        attempts = self.session.exec(select(Attempt)).all()
        
        return InstructorAnalytics(
            total_students=len(students),
            struggling_students=self._find_struggling_students(students),
            concept_heatmap=self._build_concept_heatmap(students),
            misconception_clusters=self._cluster_by_misconception(attempts, students),
            priority_students=self._rank_priority_students(students, attempts),
            intervention_suggestions=self._generate_suggestions(students, attempts)
        )
    
    def _find_struggling_students(self, students: List[Student]) -> List[int]:
        """Find students who are struggling overall."""
        struggling = []
        
        for student in students:
            mastery = student.mastery_scores or {}
            if mastery:
                avg_mastery = sum(mastery.values()) / len(mastery)
                if avg_mastery < 0.4:
                    struggling.append(student.id)
        
        return struggling
    
    def _build_concept_heatmap(self, students: List[Student]) -> Dict[str, Dict[str, int]]:
        """Build heatmap of concept mastery across students."""
        heatmap = {}
        
        for concept_id in CONCEPT_GRAPH.keys():
            heatmap[concept_id] = {"struggling": 0, "developing": 0, "mastered": 0}
        
        for student in students:
            mastery = student.mastery_scores or {}
            for concept, score in mastery.items():
                if concept not in heatmap:
                    continue
                if score < 0.4:
                    heatmap[concept]["struggling"] += 1
                elif score < 0.8:
                    heatmap[concept]["developing"] += 1
                else:
                    heatmap[concept]["mastered"] += 1
        
        return heatmap
    
    def _cluster_by_misconception(
        self, 
        attempts: List[Attempt],
        students: List[Student]
    ) -> List[StudentCluster]:
        """Cluster students by common misconceptions."""
        # Count misconceptions per student
        student_misconceptions: Dict[int, List[str]] = {}
        for attempt in attempts:
            if attempt.misconceptions:
                if attempt.student_id not in student_misconceptions:
                    student_misconceptions[attempt.student_id] = []
                student_misconceptions[attempt.student_id].extend(attempt.misconceptions)
        
        # Group by most frequent misconception
        misconception_students: Dict[str, List[int]] = {}
        for student_id, miscs in student_misconceptions.items():
            if miscs:
                # Get most common misconception for this student
                most_common = Counter(miscs).most_common(1)
                if most_common:
                    misc = most_common[0][0]
                    if misc not in misconception_students:
                        misconception_students[misc] = []
                    if student_id not in misconception_students[misc]:
                        misconception_students[misc].append(student_id)
        
        # Create clusters
        clusters = []
        for misc, student_ids in misconception_students.items():
            if len(student_ids) >= 2:  # Only create cluster if 2+ students
                misc_data = MISCONCEPTIONS.get(misc, {})
                clusters.append(StudentCluster(
                    misconception=misc,
                    students=student_ids,
                    severity=misc_data.get("severity", "medium"),
                    recommended_intervention=self._get_intervention(misc, len(student_ids))
                ))
        
        # Sort by number of students
        clusters.sort(key=lambda c: len(c.students), reverse=True)
        return clusters[:10]  # Top 10 clusters
    
    def _get_intervention(self, misconception: str, count: int) -> str:
        """Get recommended intervention for a misconception."""
        interventions = {
            "off_by_one": "Interactive demonstration of array indexing and range() behavior",
            "assignment_vs_equality": "Visual comparison exercise: = vs == in different contexts",
            "array_indexing_error": "Hands-on practice with list indexing puzzles",
            "return_vs_print": "Function output tracing exercise",
            "integer_division_confusion": "Calculator simulation comparing / and //",
            "wrong_loop_condition": "Loop tracing with varying conditions",
            "infinite_loop": "Debugging exercise: identify and fix infinite loops",
            "type_coercion_error": "Type checking interactive examples",
        }
        
        base = interventions.get(misconception, f"Targeted practice on {misconception}")
        
        if count >= 5:
            return f"GROUP SESSION: {base}"
        else:
            return f"Small group work: {base}"
    
    def _rank_priority_students(
        self,
        students: List[Student],
        attempts: List[Attempt]
    ) -> List[Dict]:
        """Rank students by need for instructor attention."""
        priority_list = []
        
        # Get attempt counts per student
        attempt_counts = Counter(a.student_id for a in attempts)
        incorrect_counts = Counter(
            a.student_id for a in attempts if not a.is_correct
        )
        
        for student in students:
            mastery = student.mastery_scores or {}
            avg_mastery = sum(mastery.values()) / max(len(mastery), 1)
            
            total_attempts = attempt_counts.get(student.id, 0)
            incorrect = incorrect_counts.get(student.id, 0)
            
            # Calculate priority score (lower is more urgent)
            priority_score = avg_mastery
            if total_attempts > 0:
                error_rate = incorrect / total_attempts
                priority_score = priority_score * 0.6 + (1 - error_rate) * 0.4
            
            priority_list.append({
                "student_id": student.id,
                "username": student.username,
                "priority_score": round(priority_score, 2),
                "avg_mastery": round(avg_mastery, 2),
                "total_attempts": total_attempts,
                "needs_attention": priority_score < 0.4
            })
        
        # Sort by priority (lowest first)
        priority_list.sort(key=lambda x: x["priority_score"])
        return priority_list[:20]  # Top 20 priority students
    
    def _generate_suggestions(
        self,
        students: List[Student],
        attempts: List[Attempt]
    ) -> List[str]:
        """Generate actionable intervention suggestions."""
        suggestions = []
        
        # Analyze overall class trends
        all_misconceptions = []
        for attempt in attempts:
            if attempt.misconceptions:
                all_misconceptions.extend(attempt.misconceptions)
        
        if all_misconceptions:
            top_miscs = Counter(all_misconceptions).most_common(3)
            for misc, count in top_miscs:
                misc_data = MISCONCEPTIONS.get(misc, {})
                concepts = misc_data.get("concepts", [])
                suggestions.append(
                    f"Address '{misc_data.get('name', misc)}' ({count} occurrences) - "
                    f"Review {', '.join(concepts[:2]) if concepts else 'related concepts'}"
                )
        
        # Check for struggling baseline groups
        baseline_mastery = {"low": [], "medium": [], "high": []}
        for student in students:
            level = student.baseline_level.value if student.baseline_level else "medium"
            mastery = student.mastery_scores or {}
            if mastery:
                avg = sum(mastery.values()) / len(mastery)
                baseline_mastery[level].append(avg)
        
        for level, masteries in baseline_mastery.items():
            if masteries and sum(masteries) / len(masteries) < 0.5:
                suggestions.append(
                    f"Consider additional support for {level}-baseline students "
                    f"(avg mastery: {sum(masteries)/len(masteries):.0%})"
                )
        
        if not suggestions:
            suggestions.append("Class is progressing well. Consider introducing more advanced topics.")
        
        return suggestions
    
    def get_student_detail(self, student_id: int) -> Optional[Dict]:
        """Get detailed analytics for a specific student."""
        student = self.session.get(Student, student_id)
        if not student:
            return None
        
        attempts = self.session.exec(
            select(Attempt).where(Attempt.student_id == student_id)
        ).all()
        
        # Build timeline
        timeline = []
        for attempt in sorted(attempts, key=lambda a: a.submitted_at or ""):
            question = self.session.get(Question, attempt.question_id)
            timeline.append({
                "timestamp": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
                "question_id": attempt.question_id,
                "concept": question.concept if question else "unknown",
                "is_correct": attempt.is_correct,
                "misconceptions": attempt.misconceptions,
                "confidence": attempt.confidence_score
            })
        
        # Calculate stats
        correct = sum(1 for a in attempts if a.is_correct)
        total = len(attempts)
        
        return {
            "student_id": student.id,
            "username": student.username,
            "baseline_level": student.baseline_level.value if student.baseline_level else "medium",
            "mastery_scores": student.mastery_scores or {},
            "current_concept": student.current_concept,
            "pretest_completed": student.pretest_completed,
            "posttest_completed": student.posttest_completed,
            "stats": {
                "total_attempts": total,
                "correct": correct,
                "accuracy": correct / max(total, 1),
                "avg_confidence": sum(a.confidence_score for a in attempts) / max(total, 1)
            },
            "timeline": timeline[-50:],  # Last 50 attempts
            "misconceptions": list(set(
                m for a in attempts for m in (a.misconceptions or [])
            ))
        }
