"""
Assessment Agent

Generates targeted assessment questions (MCQ and coding) based on concepts.
"""
import json
import re
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from app.llm import get_llm_provider
from app.db.models import QuestionType, DifficultyLevel


@dataclass
class GeneratedQuestion:
    """A generated assessment question."""
    question_type: QuestionType
    concept: str
    difficulty: DifficultyLevel
    prompt: str
    options: Optional[Dict[str, str]] = None
    correct_answer: Optional[str] = None
    starter_code: Optional[str] = None
    test_cases: Optional[Dict] = None
    solution: Optional[str] = None
    explanation: str = ""


class AssessmentAgent:
    """Generates targeted assessment questions."""
    
    def __init__(self):
        self.llm = get_llm_provider()
    
    def generate_mcq(
        self,
        concept: str,
        difficulty: str = "medium",
        misconceptions_to_test: List[str] = None,
        avoid_similar_to: List[str] = None
    ) -> GeneratedQuestion:
        """Generate a multiple choice question.
        
        Args:
            concept: The concept to test
            difficulty: easy/medium/hard
            misconceptions_to_test: Specific misconceptions to target
            avoid_similar_to: Previous questions to avoid duplicating
        """
        system_prompt = """You are an expert in creating programming assessment questions.
Create a multiple choice question that tests understanding, not just memorization.
Return JSON with: prompt, options (A/B/C/D), correct_answer, explanation.
Make distractors based on common misconceptions."""

        prompt = f"""Create a {difficulty} MCQ for: {concept}

{f"Test for misconceptions: {misconceptions_to_test}" if misconceptions_to_test else ""}
{f"Avoid similar to: {avoid_similar_to[:2]}" if avoid_similar_to else ""}

Return JSON only with: prompt, options, correct_answer, explanation"""

        try:
            response = self.llm.generate(prompt, system_prompt, temperature=0.8)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return GeneratedQuestion(
                    question_type=QuestionType.MCQ,
                    concept=concept,
                    difficulty=DifficultyLevel(difficulty),
                    prompt=data.get("prompt", ""),
                    options=data.get("options", {}),
                    correct_answer=data.get("correct_answer", ""),
                    explanation=data.get("explanation", "")
                )
        except Exception:
            pass
        
        return self._template_mcq(concept, difficulty)
    
    def generate_coding(
        self,
        concept: str,
        difficulty: str = "medium",
        misconceptions_to_test: List[str] = None
    ) -> GeneratedQuestion:
        """Generate a coding question with test cases.
        
        Args:
            concept: The concept to test
            difficulty: easy/medium/hard
            misconceptions_to_test: Specific misconceptions to target
        """
        system_prompt = """You are an expert in creating programming exercises.
Create a coding problem with clear requirements and test cases.
Return JSON with: prompt, starter_code, test_cases (array of {input, expected}), solution, explanation."""

        prompt = f"""Create a {difficulty} coding problem for: {concept}

{f"Test for misconceptions: {misconceptions_to_test}" if misconceptions_to_test else ""}

Return JSON with: prompt, starter_code, test_cases, solution, explanation"""

        try:
            response = self.llm.generate(prompt, system_prompt, temperature=0.8)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return GeneratedQuestion(
                    question_type=QuestionType.CODING,
                    concept=concept,
                    difficulty=DifficultyLevel(difficulty),
                    prompt=data.get("prompt", ""),
                    starter_code=data.get("starter_code", ""),
                    test_cases={"tests": data.get("test_cases", [])},
                    solution=data.get("solution", ""),
                    explanation=data.get("explanation", "")
                )
        except Exception:
            pass
        
        return self._template_coding(concept, difficulty)
    
    def _template_mcq(self, concept: str, difficulty: str) -> GeneratedQuestion:
        """Generate template-based MCQ."""
        templates = {
            "variables": GeneratedQuestion(
                question_type=QuestionType.MCQ,
                concept="variables",
                difficulty=DifficultyLevel(difficulty),
                prompt="What will be the value of 'result' after this code?\n\nx = 5\ny = x\nx = 10\nresult = y",
                options={
                    "A": "10",
                    "B": "5",
                    "C": "15",
                    "D": "Error"
                },
                correct_answer="B",
                explanation="When y = x is executed, y gets the VALUE of x (5), not a reference. Changing x later doesn't affect y."
            ),
            "loops": GeneratedQuestion(
                question_type=QuestionType.MCQ,
                concept="loops",
                difficulty=DifficultyLevel(difficulty),
                prompt="What will be printed?\n\nfor i in range(2, 5):\n    print(i, end=' ')",
                options={
                    "A": "2 3 4 5",
                    "B": "2 3 4",
                    "C": "1 2 3 4",
                    "D": "2 3 4 5 6"
                },
                correct_answer="B",
                explanation="range(2, 5) produces 2, 3, 4. The end value (5) is not included."
            ),
            "arrays": GeneratedQuestion(
                question_type=QuestionType.MCQ,
                concept="arrays",
                difficulty=DifficultyLevel(difficulty),
                prompt="What is the output?\n\narr = [1, 2, 3, 4, 5]\nprint(arr[1:4])",
                options={
                    "A": "[1, 2, 3, 4]",
                    "B": "[2, 3, 4]",
                    "C": "[2, 3, 4, 5]",
                    "D": "[1, 2, 3]"
                },
                correct_answer="B",
                explanation="Slicing arr[1:4] returns elements from index 1 to 3 (4 is excluded)."
            ),
        }
        
        return templates.get(concept, GeneratedQuestion(
            question_type=QuestionType.MCQ,
            concept=concept,
            difficulty=DifficultyLevel(difficulty),
            prompt=f"Which statement about {concept} is TRUE?",
            options={
                "A": f"{concept} is always required",
                "B": f"{concept} improves code organization",
                "C": f"{concept} is only for advanced users",
                "D": f"{concept} cannot be combined with other features"
            },
            correct_answer="B",
            explanation=f"{concept} is a fundamental programming concept that improves code organization."
        ))
    
    def _template_coding(self, concept: str, difficulty: str) -> GeneratedQuestion:
        """Generate template-based coding question."""
        templates = {
            "loops": GeneratedQuestion(
                question_type=QuestionType.CODING,
                concept="loops",
                difficulty=DifficultyLevel(difficulty),
                prompt="Write a function `count_even(nums)` that returns the count of even numbers in a list.",
                starter_code="def count_even(nums):\n    # Your code here\n    pass",
                test_cases={"tests": [
                    {"input": [[1, 2, 3, 4, 5, 6]], "expected": 3},
                    {"input": [[1, 3, 5]], "expected": 0},
                    {"input": [[2, 4, 6]], "expected": 3}
                ]},
                solution="def count_even(nums):\n    count = 0\n    for n in nums:\n        if n % 2 == 0:\n            count += 1\n    return count",
                explanation="Loop through the list and count numbers where n % 2 == 0."
            ),
            "arrays": GeneratedQuestion(
                question_type=QuestionType.CODING,
                concept="arrays",
                difficulty=DifficultyLevel(difficulty),
                prompt="Write a function `second_largest(nums)` that returns the second largest element in a list.",
                starter_code="def second_largest(nums):\n    # Your code here\n    pass",
                test_cases={"tests": [
                    {"input": [[1, 5, 3, 9, 2]], "expected": 5},
                    {"input": [[10, 20, 30]], "expected": 20},
                    {"input": [[5, 5, 5, 3]], "expected": 5}
                ]},
                solution="def second_largest(nums):\n    unique = list(set(nums))\n    unique.sort(reverse=True)\n    return unique[1] if len(unique) > 1 else unique[0]",
                explanation="Remove duplicates, sort descending, return second element."
            ),
        }
        
        return templates.get(concept, GeneratedQuestion(
            question_type=QuestionType.CODING,
            concept=concept,
            difficulty=DifficultyLevel(difficulty),
            prompt=f"Write a function that demonstrates {concept}.",
            starter_code=f"def solve(x):\n    # Your code here\n    pass",
            test_cases={"tests": [{"input": [1], "expected": 1}]},
            solution=f"def solve(x):\n    return x",
            explanation=f"Basic {concept} implementation."
        ))
