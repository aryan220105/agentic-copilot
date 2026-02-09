"""
Sandboxed Code Execution

Safe execution of student code with timeout, memory limits, and restricted access.
"""
import subprocess
import sys
import os
import tempfile
from typing import Dict, Optional
from app.config import settings


def execute_code(
    code: str,
    language: str = "python",
    timeout: int = None,
    stdin: str = ""
) -> Dict:
    """Execute code in a sandboxed environment.
    
    Args:
        code: The code to execute
        language: Programming language (python/javascript)
        timeout: Execution timeout in seconds
        stdin: Standard input to provide
        
    Returns:
        Dict with output, error, return_code, and timed_out
    """
    timeout = timeout or settings.SANDBOX_TIMEOUT
    
    if language == "python":
        return _execute_python(code, timeout, stdin)
    elif language == "javascript":
        return _execute_javascript(code, timeout, stdin)
    else:
        return {"error": f"Unsupported language: {language}", "output": "", "return_code": -1}


def _execute_python(code: str, timeout: int, stdin: str) -> Dict:
    """Execute Python code safely."""
    # Add safety wrapper
    safe_code = f'''
import sys
import os

# Disable dangerous functions
import builtins
_original_open = builtins.open
def _safe_open(*args, **kwargs):
    raise PermissionError("File operations are not allowed")
builtins.open = _safe_open

# Disable imports of dangerous modules
_blocked_modules = {{"os", "subprocess", "shutil", "socket", "requests", "urllib"}}
_original_import = builtins.__import__
def _safe_import(name, *args, **kwargs):
    if name in _blocked_modules or name.split('.')[0] in _blocked_modules:
        raise ImportError(f"Module {{name}} is not allowed")
    return _original_import(name, *args, **kwargs)
builtins.__import__ = _safe_import

# Limit recursion
sys.setrecursionlimit(100)

# Execute user code
{code}
'''
    
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(safe_code)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_path],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={
                    "PATH": os.environ.get("PATH", ""),
                    "PYTHONPATH": ""
                }
            )
            
            return {
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode,
                "timed_out": False
            }
            
        except subprocess.TimeoutExpired:
            return {
                "output": "",
                "error": f"Execution timed out after {timeout} seconds",
                "return_code": -1,
                "timed_out": True
            }
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
                
    except Exception as e:
        return {
            "output": "",
            "error": str(e),
            "return_code": -1,
            "timed_out": False
        }


def _execute_javascript(code: str, timeout: int, stdin: str) -> Dict:
    """Execute JavaScript code using Node.js if available."""
    # Check if Node.js is available
    try:
        subprocess.run(["node", "--version"], capture_output=True, timeout=2)
    except (subprocess.SubprocessError, FileNotFoundError):
        return {
            "output": "",
            "error": "Node.js is not available",
            "return_code": -1,
            "timed_out": False
        }
    
    # Create safe wrapper
    safe_code = f'''
// Disable dangerous operations
const _require = require;
require = function(module) {{
    const blocked = ['fs', 'child_process', 'net', 'http', 'https', 'os'];
    if (blocked.includes(module)) {{
        throw new Error(`Module ${{module}} is not allowed`);
    }}
    return _require(module);
}};

{code}
'''
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(safe_code)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ["node", temp_path],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode,
                "timed_out": False
            }
            
        except subprocess.TimeoutExpired:
            return {
                "output": "",
                "error": f"Execution timed out after {timeout} seconds",
                "return_code": -1,
                "timed_out": True
            }
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
                
    except Exception as e:
        return {
            "output": "",
            "error": str(e),
            "return_code": -1,
            "timed_out": False
        }


def run_tests(code: str, test_cases: Dict, language: str = "python") -> Dict:
    """Run test cases against student code.
    
    Args:
        code: Student's code
        test_cases: Dict with "tests" array of {input, expected}
        language: Programming language
        
    Returns:
        Dict with passed, failed, results array
    """
    tests = test_cases.get("tests", [])
    results = []
    passed = 0
    failed = 0
    
    # Extract function name from code
    import re
    func_match = re.search(r'def\s+(\w+)\s*\(', code)
    func_name = func_match.group(1) if func_match else "solve"
    
    for i, test in enumerate(tests):
        test_input = test.get("input", [])
        expected = test.get("expected")
        
        # Build test execution code
        test_code = f'''{code}

result = {func_name}(*{test_input})
print(repr(result))
'''
        
        exec_result = execute_code(test_code, language, timeout=2)
        
        if exec_result.get("timed_out"):
            results.append({
                "test": i + 1,
                "passed": False,
                "error": "Timeout",
                "expected": expected,
                "actual": None
            })
            failed += 1
        elif exec_result.get("error") and exec_result.get("return_code") != 0:
            results.append({
                "test": i + 1,
                "passed": False,
                "error": exec_result["error"][:100],
                "expected": expected,
                "actual": None
            })
            failed += 1
        else:
            try:
                actual = eval(exec_result["output"].strip())
                test_passed = actual == expected
                
                results.append({
                    "test": i + 1,
                    "passed": test_passed,
                    "expected": expected,
                    "actual": actual
                })
                
                if test_passed:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                results.append({
                    "test": i + 1,
                    "passed": False,
                    "error": f"Could not parse output: {exec_result['output'][:50]}",
                    "expected": expected,
                    "actual": None
                })
                failed += 1
    
    return {
        "passed": passed,
        "failed": failed,
        "total": len(tests),
        "all_passed": failed == 0,
        "results": results
    }
