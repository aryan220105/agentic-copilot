"""
Tests for OrchestratorAgent
"""
import pytest
from app.agents.orchestrator import OrchestratorAgent, StudentState
from app.db.models import Student, BaselineLevel, ActionType


class TestOrchestratorAgent:
    @pytest.fixture
    def orchestrator(self):
        return OrchestratorAgent()
    
    @pytest.fixture
    def mock_student(self):
        student = Student(
            id=1,
            username="test_student",
            password_hash="hash",
            baseline_level=BaselineLevel.MEDIUM,
            current_concept="variables",
            mastery_scores={"variables": 0.5, "loops": 0.3},
            pretest_completed=True
        )
        return student
    
    def test_decide_next_action_returns_decision(self, orchestrator, mock_student):
        decision = orchestrator.decide_next_action(mock_student, None)
        assert decision is not None
        assert decision.action in [ActionType.TEACH, ActionType.TEST, ActionType.RETEACH, ActionType.ADVANCE, ActionType.REVIEW]
        assert decision.concept is not None
    
    def test_get_student_progress(self, orchestrator, mock_student):
        progress = orchestrator.get_student_progress(mock_student)
        assert "current_concept" in progress
        assert "mastery_scores" in progress
        assert "overall_mastery" in progress
    
    def test_student_state_initialization(self, orchestrator, mock_student):
        state = orchestrator._get_or_create_state(mock_student)
        assert isinstance(state, StudentState)
        assert state.current_concept == "variables"
    
    def test_low_mastery_triggers_teach(self, orchestrator):
        student = Student(
            id=2,
            username="low_mastery",
            password_hash="hash",
            baseline_level=BaselineLevel.LOW,
            current_concept="loops",
            mastery_scores={"loops": 0.2},
            pretest_completed=True
        )
        decision = orchestrator.decide_next_action(student, None)
        assert decision.action in [ActionType.TEACH, ActionType.RETEACH]
