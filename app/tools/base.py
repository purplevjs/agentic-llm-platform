from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

import logging
logger = logging.getLogger(__name__)

# Base class for all tools
class BaseTool(ABC):
    def __init__(self, name, description, parameters):
        self.name = name
        self.description = description
        self.parameters = parameters

    @abstractmethod
    async def execute(self, params, context=None):
        """Run the tool with the given parameters"""
        pass

    def validate_params(self, params):
        errors = []

        # Check required params
        for param_name, param_spec in self.parameters.items():
            if param_spec.get("required", False) and param_name not in params:
                errors.append(f"Missing required parameter: {param_name}")
        
        # Check param types
        for param_name, param_value in params.items():
            if param_name not in self.parameters:
                errors.append(f"Unknown parameter: {param_name}")
                continue

            param_spec = self.parameters[param_name]
            param_type = param_spec.get("type")

            # type check
            if param_type == "string" and not isinstance(param_value, str):
                errors.append(f"Parameter {param_name} should be a string")
            elif param_type == "number" and not isinstance(param_value, (int, float)):
                errors.append(f"Parameter {param_name} should be a number")
            elif param_type == "integer" and not isinstance(param_value, int):
                errors.append(f"Parameter {param_name} should be an integer")
            elif param_type == "boolean" and not isinstance(param_value, bool):
                errors.append(f"Parameter {param_name} should be a boolean")
            elif param_type == "array" and not isinstance(param_value, list):
                errors.append(f"Parameter {param_name} should be an array")
            elif param_type == "object" and not isinstance(param_value, dict):
                errors.append(f"Parameter {param_name} should be an object")  
            

            # Check enums
            if "enum" in param_spec and param_value not in param_spec["enum"]:
                valid_values = ", ".join(str(v) for v in param_spec["enum"])
                errors.append(f"Parameter {param_name} must be one of: {valid_values}")
            

            if "minimum" in param_spec and param_value < param_spec["minimum"]:
                errors.append(f"Parameter {param_name} must be at least {param_spec['minimum']}")
            if "maximum" in param_spec and param_value > param_spec["maximum"]:
                errors.append(f"Parameter {param_name} must be at most {param_spec['maximum']}")
        
        return errors
    
    # Format the result for the agent
    def format_result(self, result):
        return{
            "tool": self.name,
            "success": True,
            "result": result if isinstance(result, (dict, str)) else str(result)
        }
    
    def format_error(self, error):
        if isinstance(error, Exception):
            error_msg = f"{type(error).__name__}: {str(error)}"
        else:
            error_msg = str(error)
        return{
            "tool": self.name,
            "success": False,
            "result": error_msg
        }


               

