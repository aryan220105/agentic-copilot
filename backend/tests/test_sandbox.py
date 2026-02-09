"""
Tests for sandbox code execution
"""
import pytest
from app.sandbox.runner import execute_code, run_tests


class TestExecuteCode:
    def test_simple_print(self):
        result = execute_code("print('hello')")
        assert result["output"].strip() == "hello"
        assert result["return_code"] == 0
        assert not result["timed_out"]
    
    def test_arithmetic(self):
        result = execute_code("print(2 + 3)")
        assert result["output"].strip() == "5"
    
    def test_timeout(self):
        result = execute_code("while True: pass", timeout=1)
        assert result["timed_out"]
    
    def test_syntax_error(self):
        result = execute_code("print(")
        assert result["return_code"] != 0
        assert "error" in result["error"].lower() or "Error" in result["error"]


class TestRunTests:
    def test_simple_function(self):
        code = """
def add(a, b):
    return a + b
"""
        test_cases = {
            "tests": [
                {"input": [1, 2], "expected": 3},
                {"input": [0, 0], "expected": 0}
            ]
        }
        result = run_tests(code, test_cases)
        assert result["passed"] == 2
        assert result["failed"] == 0
        assert result["all_passed"]
    
    def test_failing_tests(self):
        code = """
def add(a, b):
    return a - b
"""
        test_cases = {
            "tests": [
                {"input": [5, 3], "expected": 8}
            ]
        }
        result = run_tests(code, test_cases)
        assert result["passed"] == 0
        assert result["failed"] == 1
        assert not result["all_passed"]
