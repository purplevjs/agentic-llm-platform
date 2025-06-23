import logging
import aiohttp
from typing import Dict, Any, Optional

from ..config import settings
from .base import BaseTool

logger = logging.getLogger(__name__)

class WebSearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name = "web_search",
            description="Searches the web for information",
            parameters={
                "query": {
                    "type": "string",
                    "description": "Search query",
                    "required": True

                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5,
                    "required": False,
                    "minimum": 1,
                    "maximum": 10
                }
            }
        )
        self.api_key = settings.WEB_SEARCH_API_KEY

    async def execute(self, params, context=None):
        errors = self.validate_params(params)
        if errors:
            return self.format_error(",".join(errors))
        
        # get params
        query = params["query"]
        num_results = params.get("num_results", 5)


        try:
            # run search
            results = await self.search_serapi(query, num_results)
            return self.format_results(results)
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return self.format_error(str(e))
        
    
    async def search_serapi(self, query, num_results):
        if not self.api_key:
            raise ValueError("No SerAPI key configured")
        
        # setup params
        params = {
            "engine": "google",
            "q": query,
            "num": num_results,
            "api_key": self.api_key
        }

        # make request
        async with aiohttp.ClientSession() as session:
            async with session.get("https://serpapi.com/search", params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"API error: {response.status} - {error_text}")
                
                data = await response.json()
        
        # listup results
        result = []
        if "organic_results" in data:
            for result in data["organic_results"][:"num_results"]:
                result.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        return {
            "query": query,
            "result": result,
            "count": len(result)
        }
