"""
Mock LLM Provider

Deterministic template-based responses for testing and development.
No API calls required.
"""
import json
import re
from typing import Optional
from app.llm.provider import LLMProvider


class MockLLMProvider(LLMProvider):
    """Deterministic mock LLM provider for testing."""
    
    def __init__(self):
        self.call_count = 0
    
    def get_name(self) -> str:
        return "mock"
    
    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """Generate deterministic mock response based on prompt content."""
        print(f"[LLM] Mock generating (prompt length: {len(prompt)})")
        self.call_count += 1
        prompt_lower = prompt.lower()
        
        # Detect the type of request and return appropriate mock response
        if "diagnose" in prompt_lower or "misconception" in prompt_lower:
            return self._mock_diagnosis(prompt)
        elif "micro-lesson" in prompt_lower or "teach" in prompt_lower or "explain" in prompt_lower:
            return self._mock_lesson(prompt)
        elif "generate" in prompt_lower and "question" in prompt_lower:
            return self._mock_question(prompt)
        elif "verify" in prompt_lower or "validate" in prompt_lower:
            return self._mock_verification(prompt)
        elif "cluster" in prompt_lower or "group" in prompt_lower:
            return self._mock_clustering(prompt)
        else:
            return self._mock_generic(prompt)
    
    def _extract_concept(self, prompt: str) -> str:
        """Extract concept from prompt."""
        concepts = ["variables", "types", "operators", "conditionals", 
                   "loops", "functions", "arrays", "strings", "complexity"]
        for concept in concepts:
            if concept in prompt.lower():
                return concept
        return "variables"
    
    def _mock_diagnosis(self, prompt: str) -> str:
        """Generate mock diagnosis response."""
        # Check for common error patterns
        misconceptions = []
        confidence = 0.85
        
        if "=" in prompt and "==" not in prompt:
            misconceptions.append("assignment_vs_equality")
        if "range" in prompt.lower() and "len" in prompt.lower():
            misconceptions.append("off_by_one")
        if "index" in prompt.lower() or "[" in prompt:
            misconceptions.append("array_indexing_error")
        if "return" in prompt.lower() and "print" in prompt.lower():
            misconceptions.append("return_vs_print")
        if "/" in prompt and "//" not in prompt:
            misconceptions.append("integer_division_confusion")
        if "while" in prompt.lower() and "true" in prompt.lower():
            misconceptions.append("infinite_loop")
        
        if not misconceptions:
            misconceptions = ["general_misunderstanding"]
            confidence = 0.6
        
        return json.dumps({
            "misconceptions": misconceptions,
            "concept_nodes": [self._extract_concept(prompt)],
            "confidence": confidence,
            "explanation": f"Detected potential issues related to {', '.join(misconceptions)}"
        })
    
    def _mock_lesson(self, prompt: str) -> str:
        """Generate mock micro-lesson."""
        concept = self._extract_concept(prompt)
        
        lessons = {
            "variables": {
                "bullets": [
                    "Variables are containers that store data values",
                    "Use the = operator to assign values to variables",
                    "Variable names should be descriptive and follow naming conventions",
                    "Variables can be reassigned to new values at any time"
                ],
                "example": "x = 5  # Create variable x with value 5\nx = x + 1  # x is now 6\nname = 'Alice'  # String variable",
                "pitfall": "Don't confuse = (assignment) with == (comparison)",
                "quick_check": "What is the value of y after: y = 3; y = y * 2?"
            },
            "loops": {
                "bullets": [
                    "For loops iterate over a sequence (like range)",
                    "range(n) produces numbers from 0 to n-1",
                    "While loops continue until condition is False",
                    "Use break to exit a loop early"
                ],
                "example": "for i in range(3):  # i = 0, 1, 2\n    print(i)\n\ncount = 0\nwhile count < 3:\n    count += 1",
                "pitfall": "range(3) gives [0,1,2] not [1,2,3] - watch for off-by-one errors",
                "quick_check": "How many times does this loop run: for i in range(5)?"
            },
            "arrays": {
                "bullets": [
                    "Arrays/Lists store multiple values in order",
                    "Indexing starts at 0, not 1",
                    "Access elements with square brackets: arr[0]",
                    "len() returns the number of elements"
                ],
                "example": "nums = [10, 20, 30]\nfirst = nums[0]  # 10\nlast = nums[-1]  # 30\nsize = len(nums)  # 3",
                "pitfall": "Index n-1 is the last element, not index n",
                "quick_check": "What is nums[1] if nums = [5, 10, 15]?"
            },
            "functions": {
                "bullets": [
                    "Functions are reusable blocks of code",
                    "Use def to define a function",
                    "Parameters receive values when function is called",
                    "return sends a value back to the caller"
                ],
                "example": "def greet(name):\n    return 'Hello, ' + name\n\nmessage = greet('World')  # 'Hello, World'",
                "pitfall": "return exits the function; print only displays but doesn't return",
                "quick_check": "What's the difference between print(x) and return x?"
            },
            "conditionals": {
                "bullets": [
                    "if statements execute code when condition is True",
                    "elif provides additional conditions to check",
                    "else runs when no conditions are True",
                    "Only one branch executes in an if-elif-else chain"
                ],
                "example": "x = 10\nif x > 15:\n    print('big')\nelif x > 5:\n    print('medium')  # This prints\nelse:\n    print('small')",
                "pitfall": "Once a condition is True, remaining elif/else are skipped",
                "quick_check": "What prints if x = 20 and we have if x > 10: if x > 15:?"
            }
        }
        
        lesson = lessons.get(concept, lessons["variables"])
        return json.dumps(lesson)
    
    def _mock_question(self, prompt: str) -> str:
        """Generate mock question."""
        concept = self._extract_concept(prompt)
        
        if "mcq" in prompt.lower() or "multiple choice" in prompt.lower():
            return json.dumps({
                "type": "mcq",
                "concept": concept,
                "difficulty": "medium",
                "prompt": f"What is the correct way to use {concept} in Python?",
                "options": {
                    "A": "Option A - incorrect approach",
                    "B": "Option B - correct approach",
                    "C": "Option C - common mistake",
                    "D": "Option D - syntax error"
                },
                "correct_answer": "B",
                "explanation": f"Option B is correct because it properly demonstrates {concept}."
            })
        else:
            return json.dumps({
                "type": "coding",
                "concept": concept,
                "difficulty": "medium",
                "prompt": f"Write a function that demonstrates proper use of {concept}.",
                "starter_code": f"def solve_{concept}(x):\n    # Your code here\n    pass",
                "test_cases": {
                    "tests": [
                        {"input": [1], "expected": 1},
                        {"input": [5], "expected": 5}
                    ]
                },
                "solution": f"def solve_{concept}(x):\n    return x"
            })
    
    def _mock_verification(self, prompt: str) -> str:
        """Generate mock verification result."""
        return json.dumps({
            "valid": True,
            "answer_key_correct": True,
            "difficulty_aligned": True,
            "bias_detected": False,
            "hallucination_detected": False,
            "issues": [],
            "confidence": 0.9,
            "recommendation": "APPROVE"
        })
    
    def _mock_clustering(self, prompt: str) -> str:
        """Generate mock clustering result."""
        return json.dumps({
            "clusters": [
                {
                    "misconception": "off_by_one",
                    "student_count": 5,
                    "severity": "high",
                    "recommended_intervention": "Group lesson on loop boundaries"
                },
                {
                    "misconception": "array_indexing_error",
                    "student_count": 3,
                    "severity": "high",
                    "recommended_intervention": "Visual demonstration of zero-indexing"
                }
            ],
            "priority_students": [1, 2, 8],
            "overall_health": "moderate"
        })
    
    def _mock_generic(self, prompt: str) -> str:
        """Generate generic mock response."""
        return json.dumps({
            "response": "This is a mock response for testing purposes.",
            "status": "success"
        })
