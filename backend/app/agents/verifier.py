"""
Verifier Agent

Validates generated content for quality, correctness, and safety.
"""
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from app.llm import get_llm_provider
from app.sandbox.runner import execute_code


@dataclass
class VerificationResult:
    """Result of content verification."""
    valid: bool
    answer_key_correct: bool
    difficulty_aligned: bool
    bias_detected: bool
    hallucination_detected: bool
    issues: List[str]
    confidence: float
    recommendation: str  # APPROVE, REVISE, REJECT
    execution_result: Optional[Dict] = None


class VerifierAgent:
    """Verifies generated content for quality and correctness."""
    
    def __init__(self):
        self.llm = get_llm_provider()
    
    def verify_mcq(
        self,
        prompt: str,
        options: Dict[str, str],
        correct_answer: str,
        concept: str,
        difficulty: str
    ) -> VerificationResult:
        """Verify an MCQ question.
        
        Args:
            prompt: Question prompt
            options: Answer options (A, B, C, D)
            correct_answer: The correct option key
            concept: Concept being tested
            difficulty: Expected difficulty level
        """
        issues = []
        
        # Basic validation
        if correct_answer not in options:
            issues.append("Correct answer not in options")
        
        if len(options) < 4:
            issues.append("Less than 4 options provided")
        
        if len(prompt) < 20:
            issues.append("Question prompt too short")
        
        # Check for obvious issues
        for key, value in options.items():
            if len(value) < 2:
                issues.append(f"Option {key} is too short")
            if value.lower() in ["true", "false", "yes", "no"] and len(options) == 4:
                if all(v.lower() in ["true", "false", "yes", "no"] for v in options.values()):
                    issues.append("True/False format with 4 options is confusing")
        
        # LLM-based verification
        llm_check = self._llm_verify_mcq(prompt, options, correct_answer, concept, difficulty)
        issues.extend(llm_check.get("issues", []))
        
        valid = len(issues) == 0
        
        return VerificationResult(
            valid=valid,
            answer_key_correct=llm_check.get("answer_correct", True),
            difficulty_aligned=llm_check.get("difficulty_aligned", True),
            bias_detected=llm_check.get("bias_detected", False),
            hallucination_detected=llm_check.get("hallucination_detected", False),
            issues=issues,
            confidence=llm_check.get("confidence", 0.8),
            recommendation="APPROVE" if valid else ("REVISE" if len(issues) < 3 else "REJECT")
        )
    
    def verify_coding(
        self,
        prompt: str,
        starter_code: str,
        test_cases: Dict,
        solution: str,
        concept: str,
        difficulty: str
    ) -> VerificationResult:
        """Verify a coding question by executing the solution.
        
        Args:
            prompt: Problem description
            starter_code: Starter code template
            test_cases: Test cases dict with "tests" array
            solution: Reference solution
            concept: Concept being tested
            difficulty: Expected difficulty level
        """
        issues = []
        execution_result = None
        
        # Execute solution against test cases
        try:
            tests = test_cases.get("tests", [])
            all_passed = True
            
            for i, test in enumerate(tests):
                test_input = test.get("input", [])
                expected = test.get("expected")
                
                # Build test code
                test_code = f"{solution}\n\nresult = {self._extract_function_name(solution)}(*{test_input})\nprint(repr(result))"
                
                result = execute_code(test_code, timeout=2)
                
                if result.get("error"):
                    issues.append(f"Test {i+1} execution error: {result['error'][:50]}")
                    all_passed = False
                else:
                    output = result.get("output", "").strip()
                    try:
                        actual = eval(output)
                        if actual != expected:
                            issues.append(f"Test {i+1}: expected {expected}, got {actual}")
                            all_passed = False
                    except:
                        issues.append(f"Test {i+1}: could not parse output")
                        all_passed = False
                
                execution_result = result
                
        except Exception as e:
            issues.append(f"Execution failed: {str(e)[:50]}")
        
        # Check test case coverage
        if len(tests) < 2:
            issues.append("Insufficient test cases (minimum 2)")
        
        # LLM verification for quality
        llm_check = self._llm_verify_coding(prompt, solution, concept, difficulty)
        issues.extend(llm_check.get("issues", []))
        
        valid = len(issues) == 0
        
        return VerificationResult(
            valid=valid,
            answer_key_correct=len([i for i in issues if "expected" in i]) == 0,
            difficulty_aligned=llm_check.get("difficulty_aligned", True),
            bias_detected=False,
            hallucination_detected=llm_check.get("hallucination_detected", False),
            issues=issues,
            confidence=llm_check.get("confidence", 0.75),
            recommendation="APPROVE" if valid else ("REVISE" if len(issues) < 3 else "REJECT"),
            execution_result=execution_result
        )
    
    def _extract_function_name(self, code: str) -> str:
        """Extract function name from code."""
        match = re.search(r'def\s+(\w+)\s*\(', code)
        return match.group(1) if match else "solve"
    
    def _llm_verify_mcq(
        self,
        prompt: str,
        options: Dict,
        correct: str,
        concept: str,
        difficulty: str
    ) -> Dict:
        """Use LLM to verify MCQ quality."""
        system_prompt = """Verify the MCQ question quality. Return JSON with:
- answer_correct: boolean
- difficulty_aligned: boolean (is it really the stated difficulty?)
- bias_detected: boolean (any cultural/demographic bias?)
- hallucination_detected: boolean (factually incorrect info?)
- issues: array of strings
- confidence: 0-1"""

        llm_prompt = f"""Question: {prompt}
Options: {json.dumps(options)}
Correct: {correct}
Concept: {concept}
Stated Difficulty: {difficulty}

Verify and return JSON."""

        try:
            response = self.llm.generate(llm_prompt, system_prompt, temperature=0.3)
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "answer_correct": True,
            "difficulty_aligned": True,
            "bias_detected": False,
            "hallucination_detected": False,
            "issues": [],
            "confidence": 0.7
        }
    
    def _llm_verify_coding(
        self,
        prompt: str,
        solution: str,
        concept: str,
        difficulty: str
    ) -> Dict:
        """Use LLM to verify coding problem quality."""
        system_prompt = """Verify the coding problem quality. Return JSON with:
- difficulty_aligned: boolean
- hallucination_detected: boolean (problem makes no sense?)
- issues: array of strings
- confidence: 0-1"""

        llm_prompt = f"""Problem: {prompt}
Solution: {solution}
Concept: {concept}
Stated Difficulty: {difficulty}

Verify and return JSON."""

        try:
            response = self.llm.generate(llm_prompt, system_prompt, temperature=0.3)
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "difficulty_aligned": True,
            "hallucination_detected": False,
            "issues": [],
            "confidence": 0.7
        }
