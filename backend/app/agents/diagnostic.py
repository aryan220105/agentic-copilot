"""
Diagnostic Agent

Analyzes student responses to detect misconceptions.
Uses rule-based detection first, with optional LLM refinement.
"""
import re
import json
from typing import List, Dict, Optional
from dataclasses import dataclass

from app.llm import get_llm_provider
from app.db.concept_graph import MISCONCEPTIONS, get_misconceptions_for_concept


@dataclass
class DiagnosisResult:
    """Result of misconception diagnosis."""
    misconceptions: List[str]
    concept_nodes: List[str]
    confidence: float
    explanation: str
    raw_llm_response: Optional[str] = None


class DiagnosticAgent:
    """Diagnoses student misconceptions from their responses."""
    
    def __init__(self, use_llm: bool = True):
        """Initialize the diagnostic agent.
        
        Args:
            use_llm: Whether to use LLM for refinement (falls back to rules if False)
        """
        self.use_llm = use_llm
        self.llm = get_llm_provider() if use_llm else None
    
    def diagnose(
        self,
        question_prompt: str,
        student_response: str,
        correct_answer: str,
        concept: str,
        test_output: Optional[str] = None
    ) -> DiagnosisResult:
        """Diagnose misconceptions in a student's response.
        
        Args:
            question_prompt: The question that was asked
            student_response: The student's answer/code
            correct_answer: The correct answer
            concept: The concept being tested
            test_output: Output from running code (for coding questions)
            
        Returns:
            DiagnosisResult with detected misconceptions
        """
        # First, apply rule-based detection
        rule_misconceptions = self._rule_based_detection(
            student_response, concept, test_output
        )
        
        # If LLM is enabled, get refinement
        llm_response = None
        if self.use_llm and self.llm:
            try:
                llm_result = self._llm_detection(
                    question_prompt, student_response, correct_answer, 
                    concept, test_output, rule_misconceptions
                )
                llm_response = llm_result.get("raw_response")
                
                # Merge LLM misconceptions with rule-based
                llm_misconceptions = llm_result.get("misconceptions", [])
                all_misconceptions = list(set(rule_misconceptions + llm_misconceptions))
                confidence = llm_result.get("confidence", 0.7)
                explanation = llm_result.get("explanation", "")
            except Exception as e:
                # Fallback to rule-based only
                all_misconceptions = rule_misconceptions
                confidence = 0.6 if rule_misconceptions else 0.5
                explanation = f"Rule-based detection (LLM unavailable: {str(e)[:50]})"
        else:
            all_misconceptions = rule_misconceptions
            confidence = 0.7 if rule_misconceptions else 0.5
            explanation = "Rule-based detection"
        
        # Ensure we have at least the concept in concept_nodes
        concept_nodes = [concept]
        for misc in all_misconceptions:
            if misc in MISCONCEPTIONS:
                concept_nodes.extend(MISCONCEPTIONS[misc].get("concepts", []))
        concept_nodes = list(set(concept_nodes))
        
        return DiagnosisResult(
            misconceptions=all_misconceptions,
            concept_nodes=concept_nodes,
            confidence=confidence,
            explanation=explanation,
            raw_llm_response=llm_response
        )
    
    def _rule_based_detection(
        self,
        response: str,
        concept: str,
        test_output: Optional[str] = None
    ) -> List[str]:
        """Apply rule-based pattern matching for misconception detection."""
        detected = []
        
        # Get misconceptions associated with this concept
        concept_misconceptions = get_misconceptions_for_concept(concept)
        
        # Check each misconception's patterns
        for misc_id, misc_data in MISCONCEPTIONS.items():
            patterns = misc_data.get("patterns", [])
            for pattern in patterns:
                try:
                    if re.search(pattern, response, re.IGNORECASE):
                        detected.append(misc_id)
                        break
                except re.error:
                    continue
        
        # Check test output for common errors
        if test_output:
            test_lower = test_output.lower()
            
            if "indexerror" in test_lower or "index out of range" in test_lower:
                detected.append("array_indexing_error")
            if "typeerror" in test_lower:
                detected.append("type_coercion_error")
            if "nameerror" in test_lower:
                detected.append("uninitialized_variable")
            if "timeout" in test_lower or "time limit" in test_lower:
                detected.append("infinite_loop")
            if "recursionerror" in test_lower:
                detected.append("infinite_loop")
        
        # Concept-specific checks
        if concept == "loops":
            if "range(" in response and "len(" in response:
                if "<=" in response:
                    detected.append("off_by_one")
        
        if concept == "functions":
            if "print(" in response and "return" not in response:
                detected.append("return_vs_print")
        
        return list(set(detected))
    
    def _llm_detection(
        self,
        question: str,
        response: str,
        correct: str,
        concept: str,
        test_output: Optional[str],
        rule_detected: List[str]
    ) -> Dict:
        """Use LLM for deeper misconception analysis."""
        system_prompt = """You are an expert programming education diagnostician.
Analyze student code/answers to identify specific misconceptions.
Return JSON with: misconceptions (list), confidence (0-1), explanation (string).
Only include misconceptions from this list:
- off_by_one: Loop or index boundary error
- assignment_vs_equality: Using = instead of ==
- wrong_loop_condition: Incorrect loop termination
- parameter_misuse: Wrong function parameter usage
- array_indexing_error: Wrong array/list index
- integer_division_confusion: Expecting float from int division
- return_vs_print: Confusing return and print
- scope_confusion: Variable scope issues
- infinite_loop: Non-terminating loop
- type_coercion_error: Type conversion issues"""

        prompt = f"""Question: {question}

Student Response:
{response}

Correct Answer: {correct}

Concept: {concept}

{f"Test Output: {test_output}" if test_output else ""}

Already detected by rules: {rule_detected}

Analyze and return JSON with misconceptions, confidence, and explanation."""

        try:
            llm_response = self.llm.generate(prompt, system_prompt, temperature=0.3)
            
            # Try to parse JSON from response
            try:
                # Find JSON in response
                json_match = re.search(r'\{[^{}]*\}', llm_response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    result["raw_response"] = llm_response
                    return result
            except json.JSONDecodeError:
                pass
            
            return {
                "misconceptions": [],
                "confidence": 0.5,
                "explanation": "Could not parse LLM response",
                "raw_response": llm_response
            }
            
        except Exception as e:
            return {
                "misconceptions": [],
                "confidence": 0.5,
                "explanation": f"LLM error: {str(e)}",
                "raw_response": None
            }
