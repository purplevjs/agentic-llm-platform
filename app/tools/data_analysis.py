import logging
import os
import json
import tempfile
from typing import Any, Dict, List, Optional

import aiohttp
from ..config import settings
from .base import BaseTool


logger = logging.getLogger(__name__)

class DataAnalysisTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="data_analysis",
            description="Analyzes data files and returns insights",
            parameters={
                "file_path": {
                    "type": "string",
                    "description": "Path to csv or excel file",
                    "required": False
                },
                "url": {
                    "type": "string",
                    "description": "URL to csv or excel file",
                    "required": False
                },
                "operation": {
                    "type": "string",
                    "description": "Analysis operation to perform",
                    "enum": ["summary", "filter", "visualize", "aggregate"],
                    "default": "analyze",
                    "required": True
                },
                "columns": {
                    "type": "array",
                    "description": "columns to include in analysis",
                    "required": False
                },
                "filter_query": {
                    "type": "string",
                    "description": "filter query in pandas syntax",
                    "required": False
                },
                "aggregation": {
                     "type": "string",
                    "description": "filter query in pandas syntax",
                    "required": False
                },
                "group_by": {
                    "type": "string",
                    "description": "columns to group by for aggregation",
                    "required": False
                },
                "aggregation": {
                     "type": "string",
                    "description": "aggregation function to apply (sum, mean, count)",
                    "required": False
                }
                

            }
        )
        self.max_rows = settings.DATA_ANALYSIS_MAX_ROWS
    
    async def execute(self, params, context=None):
        errors = self.validate_params(params)
        if errors:
            return self.format_error(", ".join(errors))
        
        # check url or file_path is provided
        if not params.get("file_path") and not params.get("file_path"):
            return self.format_error("Either 'file_path' or 'url' must be provided")
        

        # get params
        file_path = params.get("file_path")
        url = params.get("url")
        operation = params.get("operation")
        columns = params.get("columns", [])
        filter_query = params.get("filter_query")
        group_by = params.get("group_by")
        aggregation = params.get("aggregation", "sum")

        try:
            if url:
                data_content = await self._download_file(url)
                temp_path = self._save_temp_file(data_content, url)
            else:
                temp_path = file_path

            result = self._analyze_data(
                temp_path,
                operation,
                columns,
                filter_query,
                group_by,
                aggregation
            )

            if url and temp_path:
                os.remove(temp_path)
            return self.format_result(result)
        
        except Exception as e:
            logger.error(f"Data analysis error: {e}")
            return self.format_error(str(e))
    

    async def _download_file(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download file: HTTP {response.status}")
    
    # Save content to temp file with appropriate extension
    def _save_temp_file(self, content, url):
        ext = os.path.splitext(url)[1].lower()
        if not ext:
            ext = ".csv"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            return tmp.name
        
    # Analyze data
    def _analyze_data(self, file_path, operation, columns, filter_query, group_by, aggregation):
        try:

            import pandas as pd
            
            ext = os.path.splitext(file_path)[1].lower()
            # Load data
            if ext == ".csv":
                df = pd.read_csv(file_path)
            elif ext in (".xls", ".xlsx"):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format.: {ext}")
            
            
            # Limit rows
            if len(df) > self.max_rows:
                df = df.head(self.max_rows)
            
            # Filter columns
            if columns:
                valid_columns = [col for col in columns if col in df.columns]
                if valid_columns:
                    df = df[valid_columns]
                
            # Filter query
            if filter_query:
                try:
                    df = df.query(filter_query)
                except Exception as e:
                    logger.warning(f"Invalid filter query: {e}")
            
            # Perform operation
            if operation == "summary":
                result = {
                    "shape": df.shape,
                    "columns": df.columns.tolist(),
                    "dtypes": df.dtypes.astype(str).to_dict(),
                    "summary": df.describe().to_dict(),
                    "sample": df.head(5).to_dict(orient="records")
                }

            elif operation == "filter":
                result = {
                    "filtered_shape": df.shape,
                    "data": df.head(50).to_dict(orient="records")
                }

            elif operation == "aggregate":
                if not group_by:
                    return {"error": "group_by parameter is required for aggregation"}
                
                if group_by not in df.columns:
                    return {"error": f"Column {group_by} not found in data"}
                
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

                if not numeric_cols:
                    return {"error": "No numeric columns found for aggregation"}
                
                agg_df = df.groupby(group_by)[numeric_cols].agg(aggregation)

                # perform aggregation
                result = {
                    "aggregation": aggregation,
                    "group_by": group_by,
                    "shape": agg_df.shape,
                    "data": agg_df.to_dict(orient="index")
                }

            elif operation == "visualize":
                if group_by and group_by in df.columns:
                    counts = df[group_by].value_counts().reset_index()
                    counts.columns = [group_by, 'count']

                    result = {
                        "visualization_type": "bar",
                        "x_axis": group_by,
                        "y_axis": "count",
                        "data": counts.to_dict(orient="records")
                    }
                else:
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if not numeric_cols:
                        stats = df[numeric_cols].describe().transpose()

                        result = {
                            "visualization_type": "stats",
                            "data": stats.to_dict(orient="index")
                        }
                    else:
                        result = {
                            "error": "No valid columns found for visualization"
                        }
            else:
                result = {
                    "error": f"Unsupported operation: {operation}"
                }    
            return result
        
        except ImportError:
            raise Exception("pandas not installed")




