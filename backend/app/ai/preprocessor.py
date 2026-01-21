"""
SLMS AI Pipeline - Stage 1: Preprocessor
========================================

Convert various input types to text:
- TEXT: Pass through with cleanup
- IMAGE: OCR using Gemini Vision
- EXCEL: Parse to structured text
- PDF: Extract text
"""

from typing import Optional
import logging
import io
import base64

logger = logging.getLogger(__name__)


class Preprocessor:
    """
    Preprocess input data into text format
    """
    
    def __init__(self, ai_client):
        """
        Initialize with AI client (for image OCR)
        
        Args:
            ai_client: AI client with vision capability (Gemini)
        """
        self.ai = ai_client
    
    async def process(
        self,
        content: str,
        input_type: str,
        file_data: Optional[bytes] = None,
        file_name: Optional[str] = None
    ) -> str:
        """
        Process input and return text
        
        Args:
            content: Text content or description
            input_type: Type of input (text, image, excel, pdf)
            file_data: Binary file data (for image/excel/pdf)
            file_name: Original filename
            
        Returns:
            Processed text ready for intent classification
        """
        
        if input_type == "text":
            return self._process_text(content)
        
        elif input_type == "image":
            return await self._process_image(content, file_data)
        
        elif input_type == "excel":
            return await self._process_excel(content, file_data, file_name)
        
        elif input_type == "pdf":
            return await self._process_pdf(content, file_data)
        
        else:
            logger.warning(f"Unknown input type: {input_type}, treating as text")
            return self._process_text(content)
    
    def _process_text(self, content: str) -> str:
        """
        Clean and normalize text input
        """
        if not content:
            return ""
        
        # Basic cleanup
        text = content.strip()
        
        # Normalize whitespace
        text = " ".join(text.split())
        
        # Remove excessive newlines but keep some structure
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)
        
        return text
    
    async def _process_image(
        self, 
        content: str, 
        file_data: Optional[bytes]
    ) -> str:
        """
        Extract text from image using Gemini Vision OCR
        """
        if not file_data:
            logger.warning("No image data provided")
            return content
        
        try:
            # Convert to base64
            image_base64 = base64.b64encode(file_data).decode("utf-8")
            
            # OCR prompt
            prompt = """Đây là ảnh chụp màn hình tin nhắn hoặc tài liệu logistics.
Hãy trích xuất TOÀN BỘ văn bản trong ảnh, giữ nguyên format.

Lưu ý:
- Giữ nguyên số điện thoại, biển số xe, mã đơn hàng
- Giữ nguyên ngày giờ, địa chỉ
- Nếu có bảng, format dạng text dễ đọc
- Không thêm giải thích, chỉ trả về văn bản trích xuất

Văn bản trích xuất:"""
            
            # Call AI with vision
            response = await self.ai.generate_with_image(
                prompt=prompt,
                image_base64=image_base64,
                temperature=0.1
            )
            
            extracted_text = response.get("text", "")
            
            if extracted_text:
                logger.info(f"OCR extracted {len(extracted_text)} characters")
                return extracted_text
            else:
                logger.warning("OCR returned empty text")
                return content
                
        except Exception as e:
            logger.error(f"Image OCR failed: {str(e)}")
            return content
    
    async def _process_excel(
        self,
        content: str,
        file_data: Optional[bytes],
        file_name: Optional[str]
    ) -> str:
        """
        Parse Excel file to structured text
        """
        if not file_data:
            logger.warning("No Excel data provided")
            return content
        
        try:
            import pandas as pd
            
            # Read Excel file
            excel_buffer = io.BytesIO(file_data)
            
            # Try to read with pandas
            try:
                df = pd.read_excel(excel_buffer, header=None)
            except Exception as e:
                logger.error(f"Failed to read Excel: {e}")
                return content
            
            # Convert to structured text
            text_parts = []
            
            # Add file info
            if file_name:
                text_parts.append(f"[File: {file_name}]")
            
            text_parts.append(f"[Rows: {len(df)}, Columns: {len(df.columns)}]")
            text_parts.append("")
            
            # Convert DataFrame to text
            for idx, row in df.iterrows():
                row_text = " | ".join([
                    str(cell) if pd.notna(cell) else ""
                    for cell in row
                ])
                if row_text.strip():
                    text_parts.append(row_text)
            
            result = "\n".join(text_parts)
            logger.info(f"Excel parsed: {len(df)} rows")
            
            return result
            
        except ImportError:
            logger.error("pandas not installed, cannot parse Excel")
            return content
        except Exception as e:
            logger.error(f"Excel parsing failed: {str(e)}")
            return content
    
    async def _process_pdf(
        self,
        content: str,
        file_data: Optional[bytes]
    ) -> str:
        """
        Extract text from PDF
        """
        if not file_data:
            logger.warning("No PDF data provided")
            return content
        
        try:
            # Try pypdf first
            try:
                from pypdf import PdfReader
                
                pdf_buffer = io.BytesIO(file_data)
                reader = PdfReader(pdf_buffer)
                
                text_parts = []
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"[Page {page_num + 1}]")
                        text_parts.append(page_text)
                        text_parts.append("")
                
                if text_parts:
                    result = "\n".join(text_parts)
                    logger.info(f"PDF extracted: {len(reader.pages)} pages")
                    return result
                    
            except ImportError:
                logger.warning("pypdf not installed")
            
            # Fallback to AI vision for scanned PDFs
            logger.info("Attempting PDF OCR with AI Vision")
            
            # Convert first page to image (simplified)
            # In production, use pdf2image library
            return await self._process_image(content, file_data)
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            return content


# ══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def detect_input_type(file_name: Optional[str], content_type: Optional[str]) -> str:
    """
    Detect input type from filename or content type
    
    Args:
        file_name: Original filename
        content_type: MIME content type
        
    Returns:
        Input type string (text, image, excel, pdf)
    """
    if file_name:
        ext = file_name.lower().split(".")[-1]
        
        if ext in ["xlsx", "xls", "csv"]:
            return "excel"
        elif ext in ["png", "jpg", "jpeg", "gif", "webp"]:
            return "image"
        elif ext == "pdf":
            return "pdf"
    
    if content_type:
        if "image" in content_type:
            return "image"
        elif "excel" in content_type or "spreadsheet" in content_type:
            return "excel"
        elif "pdf" in content_type:
            return "pdf"
    
    return "text"
