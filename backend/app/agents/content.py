"""
Content Agent

Generates micro-lessons with explanations, examples, and quick checks.
"""
import json
from typing import Dict, Optional
from dataclasses import dataclass, field
from app.llm import get_llm_provider


@dataclass
class MicroLesson:
    """A micro-lesson for teaching a concept."""
    concept: str
    bullets: list = field(default_factory=list)
    worked_example: str = ""
    pitfall: str = ""
    quick_check: str = ""
    misconceptions_addressed: list = field(default_factory=list)


class ContentAgent:
    """Generates personalized micro-lessons for students."""
    
    def __init__(self):
        self.llm = get_llm_provider()
    
    def generate_lesson(
        self,
        concept: str,
        misconceptions: list = None,
        student_level: str = "medium",
        previous_attempts: list = None
    ) -> MicroLesson:
        """Generate a micro-lesson for a concept.
        
        Args:
            concept: The concept to teach
            misconceptions: List of misconceptions to address
            student_level: Student's baseline level (low/medium/high)
            previous_attempts: Previous attempts for context
            
        Returns:
            MicroLesson with explanation, example, pitfall, and quick check
        """
        misconceptions = misconceptions or []
        
        system_prompt = """You are an expert programming instructor.
Create concise, effective micro-lessons for undergraduate students.
Return JSON with exactly these fields:
- bullets: array of 3-6 short explanation points
- worked_example: a code example with comments
- pitfall: one common mistake to avoid
- quick_check: a simple question to verify understanding

Keep explanations simple and focused. Use Python for examples."""

        prompt = f"""Create a micro-lesson for: {concept}

Student level: {student_level}
Misconceptions to address: {misconceptions if misconceptions else 'None specific'}

{f"Previous struggles: {previous_attempts[:3]}" if previous_attempts else ""}

Return JSON only."""

        try:
            response = self.llm.generate(prompt, system_prompt, temperature=0.7)
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return MicroLesson(
                    concept=concept,
                    bullets=data.get("bullets", []),
                    worked_example=data.get("worked_example", data.get("example", "")),
                    pitfall=data.get("pitfall", ""),
                    quick_check=data.get("quick_check", ""),
                    misconceptions_addressed=misconceptions
                )
        except Exception as e:
            pass
        
        # Fallback to template-based lesson
        return self._template_lesson(concept, misconceptions)
    
    def _template_lesson(self, concept: str, misconceptions: list) -> MicroLesson:
        """Generate a template-based lesson as fallback."""
        templates = {
            "variables": MicroLesson(
                concept="variables",
                bullets=[
                    "Variables store data values for later use",
                    "Use descriptive names like 'user_age' not 'x'",
                    "The = operator assigns a value (right) to a variable (left)",
                    "Variables can be reassigned at any time"
                ],
                worked_example="""# Creating and using variables
name = "Alice"      # String variable
age = 25            # Integer variable
height = 5.6        # Float variable

# Reassigning
age = age + 1       # Now age is 26
print(f"{name} is {age}")""",
                pitfall="Don't confuse = (assignment) with == (comparison). x = 5 assigns, x == 5 compares.",
                quick_check="After running: x = 10; x = x + 5, what is x?"
            ),
            "loops": MicroLesson(
                concept="loops",
                bullets=[
                    "for loops iterate over sequences (range, lists, strings)",
                    "range(n) gives 0 to n-1, not 1 to n",
                    "while loops continue until condition becomes False",
                    "Use break to exit early, continue to skip iteration"
                ],
                worked_example="""# For loop with range
for i in range(3):    # i = 0, 1, 2
    print(i)

# While loop
count = 0
while count < 3:
    print(count)
    count += 1        # Don't forget to update!""",
                pitfall="range(3) produces [0, 1, 2], not [1, 2, 3]. Off-by-one errors are very common!",
                quick_check="How many times will this print? for i in range(5): print(i)"
            ),
            "arrays": MicroLesson(
                concept="arrays",
                bullets=[
                    "Lists store ordered collections of items",
                    "Indexing starts at 0: first element is list[0]",
                    "Negative indices count from end: list[-1] is last",
                    "len(list) gives the number of elements"
                ],
                worked_example="""# Creating and accessing lists
fruits = ["apple", "banana", "cherry"]
first = fruits[0]     # "apple"
last = fruits[-1]     # "cherry"
count = len(fruits)   # 3

# Modifying
fruits.append("date")
fruits[0] = "apricot" """,
                pitfall="The last valid index is len(list)-1, not len(list). list[len(list)] causes IndexError!",
                quick_check="If nums = [10, 20, 30], what is nums[1]?"
            ),
            "functions": MicroLesson(
                concept="functions",
                bullets=[
                    "Functions are reusable blocks of code",
                    "def function_name(parameters): defines a function",
                    "return sends a value back to the caller",
                    "Parameters receive values when function is called"
                ],
                worked_example="""# Defining a function
def greet(name):
    message = "Hello, " + name
    return message    # Returns the value

# Calling the function
result = greet("World")
print(result)         # "Hello, World" """,
                pitfall="return vs print: return gives a value back, print just displays. x = print('hi') gives None!",
                quick_check="What's the difference between: return x and print(x)?"
            ),
            "conditionals": MicroLesson(
                concept="conditionals",
                bullets=[
                    "if checks a condition and runs code if True",
                    "elif provides additional conditions (only checked if previous False)",
                    "else runs when all conditions are False",
                    "Only ONE branch executes in an if-elif-else chain"
                ],
                worked_example="""# Conditional chain
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"       # This runs (score is 85)
elif score >= 70:
    grade = "C"       # Skipped - previous was True
else:
    grade = "F"

print(grade)          # "B" """,
                pitfall="Once a condition is True, all following elif/else blocks are skipped, even if they're also True.",
                quick_check="If x = 15, what prints? if x > 10: print('A') elif x > 5: print('B')"
            ),
        }
        
        return templates.get(concept, MicroLesson(
            concept=concept,
            bullets=[
                f"This lesson covers {concept}",
                "Practice is key to understanding",
                "Review examples carefully",
                "Try the exercises below"
            ],
            worked_example=f"# Example for {concept}\n# TODO: Add specific example",
            pitfall=f"Common mistake with {concept}: not reading documentation",
            quick_check=f"Can you explain {concept} in your own words?"
        ))
