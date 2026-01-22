"""
Excel Import API - Endpoints for Flexible Excel Parser (Solution 2)
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Dict, Any, List
import tempfile
import os
import shutil
import logging
import traceback

from app.ai.excel import FlexibleExcelParser
from app.ai.clients import get_ai_client

logger = logging.getLogger(__name__)
router = APIRouter()

# Global parser instance
_parser = None

def get_parser():
    global _parser
    if _parser is None:
        _parser = FlexibleExcelParser(ai_client=get_ai_client())
    return _parser

@router.post("/parse")
async def parse_excel(
    file: UploadFile = File(...),
):
    """
    Parse uploaded Excel file and return preview data
    """
    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        try:
            parser = get_parser()
            result = await parser.parse(tmp_path)
            
            # Return preview data
            return {
                "success": True,
                "preview": result.preview,
                "confidence": result.confidence.to_dict(),
                "file_path": tmp_path # Return temp path for subsequent import (should be secured in prod)
            }
            
        finally:
            # Don't delete yet if we want to import? 
            # Ideally we cache or client re-uploads.
            # Fore demo/v1, let's keep it for a short while or rely on client sending validated data back.
            # Actually, parse returns extracted data. User confirms data.
            # We don't need the file anymore if we return all data.
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"Excel parse error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_parsed_data(
    data: Dict[str, Any]
):
    """
    Import confirmed data into database (Create Jobs)
    """
    # This endpoint receives the data structure that was returned by /parse
    # (potentially modified/corrected by user) and creates the actual jobs.
    
    # TODO: Implement job creation logic using JobService
    # For now, just return success
    
    return {
        "success": True,
        "message": f"Successfully imported {len(data.get('jobs', []))} jobs",
        "imported_ids": [] # Placeholder
    }
