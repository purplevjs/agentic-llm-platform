import json
import logging
from typing import Any, Dict, List, Tuple
import uuid

from openai import OpenAI

from ..config import settings
from ..tools.base import BaseTool


logger = logging.getLogger(__name__)


class AgentOrchestrator:
    def __init__(self, tools=None, conversation_id= None):
        self.tools = tools or {}
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.messages = []

        self.llm_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def process_query(self, query: str, context=None) -> Dict[str, Any]:
        """
        Process a user query through the agent workflow.

        Args:
            query: The user's query string
            context: Optional context information
                
        Returns:
            Dict containing response, tool used, and results
        """
        logger.info(f"Processing query: {query}")
        if context:
            logger.info(f"With context: {context}")

        self.messages.append({"role": "user", "content": query})

        # 1. Decide which tools to use
        selected_tools = await self._select_tools(query)  # 수정: select_tools -> _select_tools
        logger.info(f"Selected tools: {[t for t, _ in selected_tools]}")

        # 2. Execute tools in sequence
        tool_results = await self._execute_tools(selected_tools, query)

        # 3. Generate final response using LLM
        response = await self._create_response(query, tool_results)

        # add response to history
        self.messages.append({"role": "assistant", "content": response})

        # Return the final result
        return {
            "conversation_id": self.conversation_id,
            "query": query,
            "response": response,
            "tools_used": [tool for tool, _ in selected_tools],
            "tool_results": {t: r for t, r in tool_results}
        }

    

    async def _select_tools(self, query: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Decide which tools to use for this query

        Args:
            query: The user's query
            
        Returns:
            List of tool_name, parameters tuples
        """

        tool_descriptions = []
        for name, tool in self.tools.items():
            tool_descriptions.append({
                "name": name,
                "description": tool.description,
                "parameters": tool.parameters
            })
        
        # System prompt
        system_prompt = """
        You are an AI assistant that decides which tools to use to answer a query.
        Select only the tools that are necessary to answer the query effectively.


        Reply with a JSON object in this format:
        {
            "tools": [
                {
                    "name": "tool_name",
                    "params": {
                        "param1": "value1",
                        "param2": "value2"
                    }
                }
            ],
            "reasoning": "Your step-by-step reasoning for selecting these tools"
        }
        """

        # Create user prompt with query and tool info
        user_prompt = f"""
        Query: {query}

        Available tools:
        {json.dumps(tool_descriptions, indent=2)}
        Select the appropriate tools and parameters to answer the query.
        """

        # Call LLM to decide tools
        try:
            response = self.llm_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            # Extract tool selections
            selected_tools = []
            for tool in data.get("tools", []):
                tool_name = tool.get("name")
                params = tool.get("params", {})

                # Only add if tool exists
                if tool_name in self.tools:
                    if tool_name == "web_search" and "query" not in params:
                        params["query"] = query

                    selected_tools.append((tool_name, params))
            
            return selected_tools
        
        except Exception as e:
            logger.error(f"Error selecting tools: {e}")
            if "web_search" in self.tools:
                return [("web_search", {"query": query})]
            return []

       
    async def _execute_tools(
        self, 
        selected_tools: List[Tuple[str, Dict[str, Any]]], 
        query: str
    ) -> List[Tuple[str, Any]]:
        """
        Execute the selected tools in sequence.
        
        Args:
            selected_tools: List of (tool_name, parameters) tuples
            query: Original user query
            
        Returns:
            List of (tool_name, result) tuples
        """
        results = []
        
        for tool_name, params in selected_tools:
            try:
                # Get the tool
                tool = self.tools[tool_name]
                
                # Add context from previous tools if needed
                context = {
                    "query": query,
                    "previous_results": results.copy() if results else None
                }
                
                # Execute tool
                logger.info(f"Executing {tool_name} with params: {params}")
                result = await tool.execute(params, context)
                results.append((tool_name, result))
                
                # Check if we need conditional tool execution
                # For example, if web search finds PDFs we might want to analyze them
                if tool_name == "web_search" and "pdf_parser" in self.tools and result.get("success", False):
                    # Look for PDF links in results
                    pdf_urls = self._extract_pdf_urls_from_search(result)
                    
                    if pdf_urls:
                        logger.info(f"Found {len(pdf_urls)} PDF URLs in search results")
                        # Only process first PDF to avoid too much processing
                        pdf_url = pdf_urls[0]
                        pdf_result = await self.tools["pdf_parser"].execute(
                            {"url": pdf_url},
                            {"query": query, "source": "search_result"}
                        )
                        results.append(("pdf_parser", pdf_result))
                
            except Exception as e:
                logger.error(f"Error executing {tool_name}: {e}")
                results.append((tool_name, {"error": str(e), "success": False}))
        
        return results
        
    
    def _extract_pdf_urls_from_search(self, search_result):
        """
        Extract PDF URLs from web search results.
        """
        pdf_urls = []
        try:
            if search_result.get("success") and "result" in search_result:  # 수정: "sucess" -> "success"
                results = search_result["result"].get("results", [])

                for result in results:
                    link = result.get("link", "")
                    if link.lower().endswith(".pdf"):
                        pdf_urls.append(link)
        except Exception as e:
            logger.error(f"Error extracting PDF URLs: {e}")
        
        return pdf_urls

    async def _create_response(self, query: str, tool_results: List[Tuple[str, Any]]) -> str:
        """
        Create the final response using the LLM based on tool results.
        
        Args:
            query: Original user query
            tool_results: List of (tool_name, result) tuples
            
        Returns:
            Final response dictionary
        """

        # format tool results for the prompt
        formatted_results = ""
        for tool_name, result in tool_results:
            if isinstance(result, dict):
                result_str = json.dumps(result, indent=2)
            else:
                result_str = str(result)
            
            formatted_results += f"**{tool_name}**:\n{result_str}\n\n"

        # System prompt
        system_prompt = """
        You are a helpful AI assistant that uses tools to answer questions accurately.
        
        When creating your response:
        1. Use the information from tool results to formulate an accurate answer
        2. Be conversational and helpful
        3. If tools were used, incorporate that information naturally
        4. If tools failed or didn't provide useful information, acknowledge that
        5. If you don't know something, be honest about it
        
        Do not reveal the specific tools that were used in your response.
        Do not mention "tool results" explicitly - incorporate the information naturally.
        """

        # Create user prompt
        user_prompt = f"Question: {query}\n\n"
        if formatted_results:
            user_prompt += f"Tool results:\n{formatted_results}"
        else:
            user_prompt += "No tools were used for this query"


        # Call LLM to generate final response
        try:
            response = self.llm_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating final response: {e}")
            return f"An error occurred while generating the response: {str(e)}"



       
            