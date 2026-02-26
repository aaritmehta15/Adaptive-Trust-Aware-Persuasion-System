"""
PDF Reader Tool for Jarvis Agent
Allows reading and extracting text from PDF files.
"""

from google.adk.tools import FunctionTool
from typing import Optional
import os


def read_pdf_file(file_path: str, page_start: Optional[int] = None, page_end: Optional[int] = None) -> str:
    """
    Read and extract text from a PDF file.
    
    Args:
        file_path: The absolute or relative path to the PDF file
        page_start: Optional starting page number (1-indexed). If not provided, starts from page 1
        page_end: Optional ending page number (1-indexed). If not provided, reads to the end
        
    Returns:
        The extracted text content from the PDF file
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        Exception: If there's an error reading the PDF
    """
    try:
        import PyPDF2
    except ImportError:
        return "Error: PyPDF2 library is not installed. Please install it with: pip install PyPDF2"
    
    # Check if file exists
    if not os.path.exists(file_path):
        return f"Error: File not found at path: {file_path}"
    
    # Check if file is a PDF
    if not file_path.lower().endswith('.pdf'):
        return f"Error: File is not a PDF: {file_path}"
    
    try:
        # Open and read the PDF
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            # Determine page range
            start = (page_start - 1) if page_start else 0
            end = page_end if page_end else num_pages
            
            # Validate page range
            if start < 0 or start >= num_pages:
                return f"Error: Invalid start page {page_start}. PDF has {num_pages} pages."
            if end > num_pages:
                end = num_pages
            
            # Extract text from pages
            text_content = []
            text_content.append(f"PDF File: {os.path.basename(file_path)}")
            text_content.append(f"Total Pages: {num_pages}")
            text_content.append(f"Reading pages {start + 1} to {end}")
            text_content.append("-" * 50)
            
            for page_num in range(start, end):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text_content.append(f"\n--- Page {page_num + 1} ---\n")
                text_content.append(page_text)
            
            result = "\n".join(text_content)
            return result
            
    except Exception as e:
        return f"Error reading PDF file: {str(e)}"


# Create the PDF reader tool
pdf_reader = FunctionTool(read_pdf_file)

