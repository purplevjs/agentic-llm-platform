import logging
import io
import sys
import traceback
from typing import Dict, Any, Optional
import contextlib
import time

from .base import BaseTool
from ..config import settings

logger = logging.getLogger(__name__)


class CodeExecuteTool(BaseTool):
    def __init__(self):
        super().__init__(
            name = "code_execute",
            description = "Executes python code and returns the results",
            parameters = {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                    "required": True
                },
                "timeout": {
                    "type": "integer",
                    "description": "Maximum execution time in seconds",
                    "default": 10,
                    "required": False,
                    "minimum": 1,
                    "maximum": 60
                }
            })
        

        # Define allowed and blocked modules for security
        self.allowed_modules = {
            "pandas", "numpy", "matplotlib", "seaborn", 
            "sklearn", "datetime", "json", "math", 
            "random", "re", "collections", "itertools",
            "functools", "statistics"
        }

        self.blocked_modules = {
            "os", "sys", "subprocess", "socket", "requests", 
            "urllib", "http", "ftplib", "telnetlib", "smtplib",
            "ssl", "pathlib", "shutil", "tempfile", "io", 
            "pickle", "importlib", "__builtins__"
        }
    
    async def execute(self, params, context=None):
        # validate params
        errors = self.validate_params(params)
        if errors:
            return self.format_error(",".join(errors))
        
        # get params
        code = params["code"]
        timeout = params.get("timeout", 10)

        # Check code for security
        security_errors = self.check_code_security(code)
        if security_errors:
            return self.format_error(f"Security error: {', '.join(security_errors)}")
        

        try:
            # Execute code
            result = self._execute_code(code, timeout)
            return self.format_result
            

        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return self.format_error(str(e))
        

    
    def _check_code_security(self, code):
        issues = []

        # check for blocked imports
        for module in self.blocked_modules:
            if f"import {module}" in code or f"from {module}" in code:
                issues.append(f"Blocked module import: {module}")
        

        # check for dangerous functions
        dangerous_funcs = ["eval(", "exec(", "__import__("]
        for func in dangerous_funcs:
            if func in code:
                issues.append(f"Blocked function usage: {func.strip('(')}")


        # check for attribute access on blocked modules
        for module in self.blocked_modules:
            if f"{module}." in code:
                issues.append(f"Blocked attribute access on module: {module}")
        

        return issues
    
    

    def _execute_code(self, code, timeout):
        # string for IO for stdout/stderr capture
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()


        # execute environment
        execution_globals = {
            "__name__": "__main__",
        }

        # allow only certain imports
        original_import = __import__

        def secure_import(name, *args, **kwargs):
            if name in self.blocked_modules:
                raise ImportError(f"Import of {name} is not allowed")
            if name not in self.allowed_modules and all(not name.startswith(m + '.') for m in self.allowed_modules):
                raise ImportError(f"Module {name} is not allowed")
            return original_import(name, *args, **kwargs)


        # Track execution time
        start_time = time.time()
        execution_timeout = False
        execution_error = None



        # Replace builtin import
        try:
            __builtins__.__import__ = secure_import
        except:
            pass

        # Execute with captured output
        with contextlib.redirect_stdout(stdout_capture), \
             contextlib.redirect_stderr(stderr_capture):
            try:
                # Use exec with timeout check
                def exec_with_timeout():
                    exec(code, execution_globals)

                # Simple timeout implementation
                while time.time() - start_time < timeout:
                    try:
                        exec_with_timeout()
                        break
                    except Exception as e:
                        execution_error = e
                        break
                else:
                    execution_timeout = True
            except Exception as e:
                execution_error = e
        
        # Restore original import
        try:
            __builtins__.__import__ = original_import
        except:
            pass

        # get caputred output
        stdout = stdout_capture.getvalue()
        stderr = stderr_capture.getvalue()


        result = {
            "stdout": stdout,
            "stderr": stderr,
            "execution_time": time.time() - start_time
        }

        # handle timeout
        if execution_timeout:
            result["error"] = f"Execution timed out after {timeout} seconds"

        
        # handle execution error
        if execution_error:
            result["error"] = str(execution_error)
            result["traceback"] = traceback.format_exc()

        return result


            

