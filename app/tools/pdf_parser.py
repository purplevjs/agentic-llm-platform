import logging
import os
import tempfile
from typing import Dict, Any, Optional

import aiohttp
from .base import BaseTool
from ..config import settings

logger = logging.getLogger(__name__)


class PDFParserTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="pdf_parser",
            description="Extracts text and data from PDF documents",
            parameters={
                "url": {
                    "type": "string",
                    "description": "URL to PDF file",
                    "required": False
                },
                "file_path": {
                    "type": "string",
                    "description": "Local path to PDF",
                    "required": False
                },
                "pages": {
                    "type": "string",
                    "description": "Pages to extract (e.g. '1-5' or '1,3,5')",
                    "required": False
                }
            }
        )
        self.max_pages = settings.PDF_MAX_PAGES

    async def execute(self, params, context=None):
        # validate params
        errors = self.validate_params(params)
        if errors:
            return self.format_error(",".join(errors))
        

        # Check url or file_path is provided
        if not params.get("url") and not params.get("file_path"):
            return self.format_error("Url and file_path is required")
        
        url = params.get("url")
        file_path = params.get("file_path")
        pages = params.get("pages")

        try:
            if url:
                pdf_content = await self._download_pdf(url)
                temp_path = self._save_temp_pdf(pdf_content)
            else:
                temp_path = file_path
            
            page_numbers = self._parse_page_range(pages)

            content = self._extract_pdf_content(temp_path, page_numbers)

            if url and temp_path:
                os.remove(temp_path)
            return self.format_result(content)
        
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            return self.format_error(e)
        
    async def _download_pdf(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download PDF: HTTP {response.status}")
                
                content_type = response.headers.get("Content-Type", "")
                if "application/pdf" not in content_type and not url.lower().endswith(".pdf"):
                    raise Exception(f"URL does not point to a PDF document")
                
                return await response.read()


    def _save_temp_pdf(self, content):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            return tmp.name

    def _parse_page_range(self, pages_str):
        if not pages_str:
            return []
        
        page_numbers = []
        parts = pages_str.split(",")

        for part in parts:
            part = part.strip()

            if "-" in part:
                start, end = part.split("-")
                try:
                    start_num = int(start.strip())
                    end_num = int(end.strip())

                    if end_num < start_num:
                        start_num, end_num = end_num, start_num
                    
                    page_numbers.extend(range(start_num, end_num + 1))
                except ValueError:
                    continue
            else:
                # Single page number
                try:
                    page_numbers.append(int(part))
                except ValueError:
                    continue

        page_numbers = sorted(set(page_numbers))

        if len(page_numbers) > self.max_pages:
            page_numbers = page_numbers[:self.max_pages]
        
        return page_numbers



    def _extract_pdf_content(self, pdf_path, page_numbers):
        try:
            import fitz

            doc = fitz.open(pdf_path)
            total_pages = doc.page_count

            if not page_numbers:
                page_numbers = list(range(1, min(total_pages + 1, self.max_pages + 1)))
            
            page_numbers = [p for p in page_numbers if 1 <= p <= total_pages]


            result = {
                "metadata": {
                    "title": doc.metadata.get("title", ""),
                    "author": doc.metadata.get("author", ""),
                    "total_pages": total_pages
                },
                "pages": []
            }

            for page_num in page_numbers:
                page = doc[page_num-1]
                text = page.get_text()

                result["pages"].append({
                    "page_number": page_num,
                    "text": text
                })
            
            return result
        
        except ImportError:
            raise Exception("PyMuPDF (fitz) not installed")

