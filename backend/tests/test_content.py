"""
Tests for ContentAgent
"""
import pytest
from app.agents.content import ContentAgent, MicroLesson


class TestContentAgent:
    @pytest.fixture
    def agent(self):
        return ContentAgent()
    
    def test_generate_lesson_returns_microlesson(self, agent):
        lesson = agent.generate_lesson(
            concept="variables",
            misconceptions=["variable_immutability"],
            student_level="medium"
        )
        assert isinstance(lesson, MicroLesson)
        assert lesson.concept == "variables"
        assert len(lesson.bullets) > 0
    
    def test_generate_lesson_fallback(self, agent):
        lesson = agent.generate_lesson(
            concept="loops",
            misconceptions=[],
            student_level="low"
        )
        assert isinstance(lesson, MicroLesson)
        assert lesson.worked_example is not None
    
    def test_all_concepts_have_fallback(self, agent):
        concepts = ["variables", "loops", "arrays", "functions", "conditionals"]
        for concept in concepts:
            lesson = agent.generate_lesson(
                concept=concept,
                misconceptions=[],
                student_level="medium"
            )
            assert isinstance(lesson, MicroLesson)
            assert len(lesson.bullets) > 0
