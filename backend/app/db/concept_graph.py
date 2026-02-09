"""
Concept Graph for Introductory Programming.

Defines the prerequisite relationships between concepts and
associated common misconceptions.
"""
from typing import Dict, List
from app.db.models import ConceptNode


# ─────────────────────────────────────────────────────────────
# CONCEPT GRAPH DEFINITION
# ─────────────────────────────────────────────────────────────

CONCEPT_GRAPH: Dict[str, ConceptNode] = {
    "variables": ConceptNode(
        id="variables",
        name="Variables",
        description="Storing and naming data values",
        prerequisites=[],
        misconceptions=["assignment_vs_equality", "uninitialized_variable"]
    ),
    "types": ConceptNode(
        id="types",
        name="Data Types",
        description="Integer, float, string, boolean types",
        prerequisites=["variables"],
        misconceptions=["integer_division_confusion", "type_coercion_error"]
    ),
    "operators": ConceptNode(
        id="operators",
        name="Operators",
        description="Arithmetic, comparison, and logical operators",
        prerequisites=["variables", "types"],
        misconceptions=["operator_precedence_error", "assignment_vs_equality"]
    ),
    "conditionals": ConceptNode(
        id="conditionals",
        name="Conditionals",
        description="If-else statements and boolean logic",
        prerequisites=["operators"],
        misconceptions=["wrong_condition_logic", "missing_else_case"]
    ),
    "loops": ConceptNode(
        id="loops",
        name="Loops",
        description="For and while loops for repetition",
        prerequisites=["conditionals"],
        misconceptions=["off_by_one", "wrong_loop_condition", "infinite_loop"]
    ),
    "functions": ConceptNode(
        id="functions",
        name="Functions",
        description="Defining and calling functions",
        prerequisites=["variables"],
        misconceptions=["parameter_misuse", "return_vs_print", "scope_confusion"]
    ),
    "arrays": ConceptNode(
        id="arrays",
        name="Arrays/Lists",
        description="Ordered collections of elements",
        prerequisites=["loops", "variables"],
        misconceptions=["array_indexing_error", "off_by_one", "empty_array_access"]
    ),
    "strings": ConceptNode(
        id="strings",
        name="Strings",
        description="Text manipulation and operations",
        prerequisites=["arrays", "types"],
        misconceptions=["string_immutability", "off_by_one", "escape_character_error"]
    ),
    "complexity": ConceptNode(
        id="complexity",
        name="Complexity Basics",
        description="Big-O notation fundamentals",
        prerequisites=["loops", "arrays"],
        misconceptions=["complexity_analysis_error", "nested_loop_complexity"]
    ),
}


# ─────────────────────────────────────────────────────────────
# MISCONCEPTION DEFINITIONS
# ─────────────────────────────────────────────────────────────

MISCONCEPTIONS: Dict[str, dict] = {
    "off_by_one": {
        "name": "Off-by-One Error",
        "description": "Loop or index boundary is one more or less than intended",
        "concepts": ["loops", "arrays", "strings"],
        "severity": "high",
        "patterns": [
            r"range\s*\(\s*\d+\s*,\s*len\s*\(",
            r"\[len\s*\([^)]+\)\s*\]",
            r"<=\s*len\s*\("
        ]
    },
    "assignment_vs_equality": {
        "name": "Assignment vs Equality Confusion",
        "description": "Using = when == is intended, or vice versa",
        "concepts": ["variables", "operators", "conditionals"],
        "severity": "high",
        "patterns": [
            r"if\s+\w+\s*=\s*[^=]",
        ]
    },
    "wrong_loop_condition": {
        "name": "Wrong Loop Condition",
        "description": "Loop termination condition is incorrect",
        "concepts": ["loops"],
        "severity": "medium",
        "patterns": []
    },
    "parameter_misuse": {
        "name": "Parameter Misuse",
        "description": "Incorrect use of function parameters",
        "concepts": ["functions"],
        "severity": "medium",
        "patterns": []
    },
    "array_indexing_error": {
        "name": "Array Indexing Error",
        "description": "Accessing array with incorrect index",
        "concepts": ["arrays"],
        "severity": "high",
        "patterns": [
            r"\[\s*-1\s*\]",
            r"\[\s*len\s*\("
        ]
    },
    "integer_division_confusion": {
        "name": "Integer Division Confusion",
        "description": "Expecting float result from integer division",
        "concepts": ["types", "operators"],
        "severity": "medium",
        "patterns": [
            r"\d+\s*/\s*\d+",
        ]
    },
    "return_vs_print": {
        "name": "Return vs Print Confusion",
        "description": "Using print when return is needed or vice versa",
        "concepts": ["functions"],
        "severity": "high",
        "patterns": [
            r"def\s+\w+[^:]+:\s*\n\s+print\s*\(",
        ]
    },
    "scope_confusion": {
        "name": "Variable Scope Confusion",
        "description": "Misunderstanding variable scope rules",
        "concepts": ["functions", "variables"],
        "severity": "medium",
        "patterns": []
    },
    "infinite_loop": {
        "name": "Infinite Loop",
        "description": "Loop that never terminates",
        "concepts": ["loops"],
        "severity": "high",
        "patterns": [
            r"while\s+True\s*:",
        ]
    },
    "type_coercion_error": {
        "name": "Type Coercion Error",
        "description": "Incorrect assumptions about type conversion",
        "concepts": ["types"],
        "severity": "medium",
        "patterns": []
    },
    "operator_precedence_error": {
        "name": "Operator Precedence Error",
        "description": "Incorrect order of operations",
        "concepts": ["operators"],
        "severity": "low",
        "patterns": []
    },
    "wrong_condition_logic": {
        "name": "Wrong Condition Logic",
        "description": "Boolean logic error in conditions",
        "concepts": ["conditionals"],
        "severity": "medium",
        "patterns": [
            r"and\s+not\s+",
            r"or\s+not\s+",
        ]
    },
    "missing_else_case": {
        "name": "Missing Else Case",
        "description": "Not handling all possible conditions",
        "concepts": ["conditionals"],
        "severity": "low",
        "patterns": []
    },
    "string_immutability": {
        "name": "String Immutability",
        "description": "Trying to modify string in place",
        "concepts": ["strings"],
        "severity": "medium",
        "patterns": [
            r"\w+\[\d+\]\s*=",
        ]
    },
    "escape_character_error": {
        "name": "Escape Character Error",
        "description": "Incorrect use of escape characters",
        "concepts": ["strings"],
        "severity": "low",
        "patterns": []
    },
    "empty_array_access": {
        "name": "Empty Array Access",
        "description": "Accessing elements of empty array",
        "concepts": ["arrays"],
        "severity": "high",
        "patterns": []
    },
    "complexity_analysis_error": {
        "name": "Complexity Analysis Error",
        "description": "Incorrect Big-O analysis",
        "concepts": ["complexity"],
        "severity": "medium",
        "patterns": []
    },
    "nested_loop_complexity": {
        "name": "Nested Loop Complexity",
        "description": "Misunderstanding complexity of nested loops",
        "concepts": ["complexity", "loops"],
        "severity": "medium",
        "patterns": []
    },
    "uninitialized_variable": {
        "name": "Uninitialized Variable",
        "description": "Using variable before assignment",
        "concepts": ["variables"],
        "severity": "high",
        "patterns": []
    },
}


# ─────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_concept(concept_id: str) -> ConceptNode:
    """Get a concept by ID."""
    return CONCEPT_GRAPH.get(concept_id)


def get_prerequisites(concept_id: str) -> List[str]:
    """Get prerequisites for a concept."""
    concept = CONCEPT_GRAPH.get(concept_id)
    return concept.prerequisites if concept else []


def get_all_prerequisites(concept_id: str) -> List[str]:
    """Get all prerequisites recursively."""
    visited = set()
    result = []
    
    def dfs(cid: str):
        if cid in visited:
            return
        visited.add(cid)
        concept = CONCEPT_GRAPH.get(cid)
        if concept:
            for prereq in concept.prerequisites:
                dfs(prereq)
            if cid != concept_id:
                result.append(cid)
    
    dfs(concept_id)
    return result


def get_concepts_by_misconception(misconception_id: str) -> List[str]:
    """Get concepts associated with a misconception."""
    misc = MISCONCEPTIONS.get(misconception_id)
    return misc.get("concepts", []) if misc else []


def get_recommended_order() -> List[str]:
    """Get recommended learning order based on prerequisites."""
    return [
        "variables",
        "types",
        "operators",
        "conditionals",
        "loops",
        "functions",
        "arrays",
        "strings",
        "complexity",
    ]


def get_misconceptions_for_concept(concept_id: str) -> List[str]:
    """Get misconceptions associated with a concept."""
    concept = CONCEPT_GRAPH.get(concept_id)
    return concept.misconceptions if concept else []
