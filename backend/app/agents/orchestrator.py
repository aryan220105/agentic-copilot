"""
Orchestrator Agent

Central coordinator that maintains student state and decides learning actions.
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.db.models import ActionType, Student, Attempt
from app.db.concept_graph import (
    CONCEPT_GRAPH, 
    get_recommended_order,
    get_prerequisites,
    get_all_prerequisites
)
from app.agents.diagnostic import DiagnosticAgent, DiagnosisResult
from app.agents.content import ContentAgent, MicroLesson
from app.agents.assessment import AssessmentAgent, GeneratedQuestion


class MasteryLevel(Enum):
    """Student mastery levels."""
    NOT_STARTED = 0
    STRUGGLING = 1
    DEVELOPING = 2
    PROFICIENT = 3
    MASTERED = 4


@dataclass
class StudentState:
    """Current state of a student in the learning system."""
    student_id: int
    current_concept: str
    mastery_scores: Dict[str, float] = field(default_factory=dict)
    misconceptions_history: List[str] = field(default_factory=list)
    recent_attempts: List[Dict] = field(default_factory=list)
    consecutive_correct: int = 0
    consecutive_incorrect: int = 0
    last_action: Optional[ActionType] = None


@dataclass
class OrchestratorDecision:
    """Decision made by the orchestrator."""
    action: ActionType
    concept: str
    reason: str
    content: Optional[Dict] = None
    question: Optional[Dict] = None


class OrchestratorAgent:
    """Coordinates the adaptive learning loop."""
    
    # Thresholds for mastery decisions
    MASTERY_THRESHOLD = 0.8
    STRUGGLING_THRESHOLD = 0.4
    ADVANCE_STREAK = 3
    RETEACH_STREAK = 2
    
    def __init__(self):
        self.diagnostic = DiagnosticAgent()
        self.content = ContentAgent()
        self.assessment = AssessmentAgent()
        self.student_states: Dict[int, StudentState] = {}
    
    def get_or_create_state(self, student: Student) -> StudentState:
        """Get or create student state."""
        if student.id not in self.student_states:
            self.student_states[student.id] = StudentState(
                student_id=student.id,
                current_concept=student.current_concept or get_recommended_order()[0],
                mastery_scores=student.mastery_scores or {}
            )
        return self.student_states[student.id]
    
    def decide_next_action(
        self,
        student: Student,
        last_attempt: Optional[Attempt] = None
    ) -> OrchestratorDecision:
        """Decide the next action for a student.
        
        Args:
            student: The student
            last_attempt: Their most recent attempt (if any)
            
        Returns:
            OrchestratorDecision with action, concept, and reason
        """
        state = self.get_or_create_state(student)
        
        # Process the last attempt if provided
        if last_attempt:
            self._process_attempt(state, last_attempt)
        
        # Get current concept mastery
        current_mastery = state.mastery_scores.get(state.current_concept, 0.0)
        
        # Decision logic
        if state.consecutive_correct >= self.ADVANCE_STREAK:
            # Student is doing well - advance or review
            if current_mastery >= self.MASTERY_THRESHOLD:
                return self._decide_advance(state)
            else:
                return self._decide_test(state, "Verify mastery before advancing")
        
        elif state.consecutive_incorrect >= self.RETEACH_STREAK:
            # Student is struggling - reteach
            return self._decide_reteach(state)
        
        elif state.last_action == ActionType.TEACH:
            # Just taught - now test
            return self._decide_test(state, "Assess understanding after lesson")
        
        elif current_mastery < self.STRUGGLING_THRESHOLD:
            # Low mastery - teach first
            return self._decide_teach(state)
        
        else:
            # Default - continue testing
            return self._decide_test(state, "Continue assessment")
    
    def _process_attempt(self, state: StudentState, attempt: Attempt) -> None:
        """Update state based on an attempt."""
        state.recent_attempts.append({
            "question_id": attempt.question_id,
            "is_correct": attempt.is_correct,
            "misconceptions": attempt.misconceptions,
            "timestamp": attempt.submitted_at.isoformat() if attempt.submitted_at else None
        })
        
        # Keep only last 10 attempts
        state.recent_attempts = state.recent_attempts[-10:]
        
        # Update consecutive counters
        if attempt.is_correct:
            state.consecutive_correct += 1
            state.consecutive_incorrect = 0
        else:
            state.consecutive_incorrect += 1
            state.consecutive_correct = 0
            # Track misconceptions
            state.misconceptions_history.extend(attempt.misconceptions)
        
        # Update mastery score
        self._update_mastery(state, attempt)
    
    def _update_mastery(self, state: StudentState, attempt: Attempt) -> None:
        """Update mastery score for current concept."""
        concept = state.current_concept
        current = state.mastery_scores.get(concept, 0.5)
        
        # Exponential moving average
        alpha = 0.3
        new_value = 1.0 if attempt.is_correct else 0.0
        
        # Confidence-weighted update
        if attempt.confidence_score > 0:
            weight = attempt.confidence_score
        else:
            weight = 1.0
        
        updated = current * (1 - alpha * weight) + new_value * (alpha * weight)
        state.mastery_scores[concept] = max(0.0, min(1.0, updated))
    
    def _decide_teach(self, state: StudentState) -> OrchestratorDecision:
        """Decide to teach the current concept."""
        # Get recent misconceptions for this concept
        recent_misc = list(set(state.misconceptions_history[-5:]))
        
        lesson = self.content.generate_lesson(
            concept=state.current_concept,
            misconceptions=recent_misc
        )
        
        state.last_action = ActionType.TEACH
        
        return OrchestratorDecision(
            action=ActionType.TEACH,
            concept=state.current_concept,
            reason=f"Teaching {state.current_concept} to address gaps",
            content={
                "bullets": lesson.bullets,
                "worked_example": lesson.worked_example,
                "pitfall": lesson.pitfall,
                "quick_check": lesson.quick_check
            }
        )
    
    def _decide_test(self, state: StudentState, reason: str) -> OrchestratorDecision:
        """Decide to test the current concept."""
        current_mastery = state.mastery_scores.get(state.current_concept, 0.5)
        
        # Determine difficulty based on mastery
        if current_mastery < 0.4:
            difficulty = "easy"
        elif current_mastery < 0.7:
            difficulty = "medium"
        else:
            difficulty = "hard"
        
        # Generate question
        question = self.assessment.generate_mcq(
            concept=state.current_concept,
            difficulty=difficulty,
            misconceptions_to_test=list(set(state.misconceptions_history[-3:]))
        )
        
        state.last_action = ActionType.TEST
        
        return OrchestratorDecision(
            action=ActionType.TEST,
            concept=state.current_concept,
            reason=reason,
            question={
                "type": question.question_type.value,
                "prompt": question.prompt,
                "options": question.options,
                "difficulty": question.difficulty.value
            }
        )
    
    def _decide_reteach(self, state: StudentState) -> OrchestratorDecision:
        """Decide to reteach - focus on identified misconceptions."""
        # Consolidate recent misconceptions
        recent_misc = list(set(state.misconceptions_history[-5:]))
        
        lesson = self.content.generate_lesson(
            concept=state.current_concept,
            misconceptions=recent_misc,
            previous_attempts=state.recent_attempts[-3:]
        )
        
        state.consecutive_incorrect = 0
        state.last_action = ActionType.RETEACH
        
        return OrchestratorDecision(
            action=ActionType.RETEACH,
            concept=state.current_concept,
            reason=f"Reteaching due to repeated difficulties with: {recent_misc[:3]}",
            content={
                "bullets": lesson.bullets,
                "worked_example": lesson.worked_example,
                "pitfall": lesson.pitfall,
                "quick_check": lesson.quick_check,
                "addressing_misconceptions": recent_misc
            }
        )
    
    def _decide_advance(self, state: StudentState) -> OrchestratorDecision:
        """Decide to advance to next concept."""
        learning_order = get_recommended_order()
        
        try:
            current_idx = learning_order.index(state.current_concept)
            if current_idx < len(learning_order) - 1:
                next_concept = learning_order[current_idx + 1]
            else:
                # Completed all concepts - review
                return self._decide_review(state)
        except ValueError:
            next_concept = learning_order[0]
        
        # Check prerequisites
        prereqs = get_prerequisites(next_concept)
        for prereq in prereqs:
            if state.mastery_scores.get(prereq, 0) < self.STRUGGLING_THRESHOLD:
                # Need to master prerequisite first
                state.current_concept = prereq
                return self._decide_teach(state)
        
        state.current_concept = next_concept
        state.consecutive_correct = 0
        state.last_action = ActionType.ADVANCE
        
        return OrchestratorDecision(
            action=ActionType.ADVANCE,
            concept=next_concept,
            reason=f"Mastered previous concept, advancing to {next_concept}"
        )
    
    def _decide_review(self, state: StudentState) -> OrchestratorDecision:
        """Decide to review - find weakest concept."""
        # Find concept with lowest mastery
        weakest = None
        lowest = 1.0
        
        for concept in get_recommended_order():
            mastery = state.mastery_scores.get(concept, 0.5)
            if mastery < lowest:
                lowest = mastery
                weakest = concept
        
        if weakest and lowest < self.MASTERY_THRESHOLD:
            state.current_concept = weakest
            state.last_action = ActionType.REVIEW
            
            return OrchestratorDecision(
                action=ActionType.REVIEW,
                concept=weakest,
                reason=f"Reviewing {weakest} (mastery: {lowest:.1%})"
            )
        
        # All mastered - comprehensive review
        state.last_action = ActionType.REVIEW
        return OrchestratorDecision(
            action=ActionType.REVIEW,
            concept=state.current_concept,
            reason="All concepts mastered! Comprehensive review."
        )
    
    def get_student_progress(self, student: Student) -> Dict:
        """Get comprehensive progress data for a student."""
        state = self.get_or_create_state(student)
        
        return {
            "current_concept": state.current_concept,
            "mastery_scores": state.mastery_scores,
            "overall_mastery": sum(state.mastery_scores.values()) / max(len(state.mastery_scores), 1),
            "misconceptions_history": list(set(state.misconceptions_history)),
            "recent_attempts": state.recent_attempts[-5:],
            "consecutive_correct": state.consecutive_correct,
            "concepts_completed": [
                c for c, m in state.mastery_scores.items() 
                if m >= self.MASTERY_THRESHOLD
            ]
        }
