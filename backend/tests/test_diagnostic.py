"""
Tests for DiagnosticAgent
"""
import pytest
from app.agents.diagnostic import DiagnosticAgent, DiagnosisResult


class TestDiagnosticAgent:
    @pytest.fixture
    def agent(self):
        return DiagnosticAgent()
    
    def test_diagnose_returns_result(self, agent):
        result = agent.diagnose(
            question_prompt="What is the value of x after: x = 5",
            student_response="10",
            correct_answer="5",
            concept="variables"
        )
        assert isinstance(result, DiagnosisResult)
        assert isinstance(result.misconceptions, list)
        assert 0 <= result.confidence <= 1
    
    def test_rule_based_variable_misconception(self, agent):
        result = agent.diagnose(
            question_prompt="What is the value of x after: x = 5; x = 10",
            student_response="5",
            correct_answer="10",
            concept="variables"
        )
        assert len(result.misconceptions) > 0
        assert result.source == "rule_based"
    
    def test_empty_response(self, agent):
        result = agent.diagnose(
            question_prompt="Test",
            student_response="",
            correct_answer="answer",
            concept="variables"
        )
        assert isinstance(result, DiagnosisResult)
    
    def test_correct_answer_no_misconceptions(self, agent):
        result = agent.diagnose(
            question_prompt="What is 2+2?",
            student_response="4",
            correct_answer="4",
            concept="operators"
        )
        assert len(result.misconceptions) == 0 or result.confidence < 0.5
