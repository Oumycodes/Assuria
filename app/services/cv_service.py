"""
Computer Vision service for analyzing images, PDFs, and videos.
Extracts text (OCR), detects objects/damage, and provides metadata.
All dependencies are optional for MVP mode.
"""

import logging
from typing import Dict, Any, List, Optional, BinaryIO
import io
import json

logger = logging.getLogger(__name__)

# Optional imports - gracefully handle missing dependencies
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL/Pillow not available - image processing disabled")

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not available - OCR disabled")

try:
    import PyPDF2
    PDF2_AVAILABLE = True
except ImportError:
    PDF2_AVAILABLE = False
    logger.warning("PyPDF2 not available - PDF processing disabled")

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not available - video processing disabled")


def analyze_image(image_data: bytes, filename: str) -> Dict[str, Any]:
    """
    Analyze an image file: OCR text extraction and basic object detection.
    Works even if CV dependencies are missing (returns basic metadata).
    
    Args:
        image_data: Raw image bytes
        filename: Original filename
        
    Returns:
        Dictionary with extracted metadata and text
    """
    # If dependencies not available, return basic info
    if not PIL_AVAILABLE:
        return {
            "type": "image",
            "filename": filename,
            "error": "PIL/Pillow not available",
            "confidence": 0.0
        }
    
    try:
        # Load image
        image = Image.open(io.BytesIO(image_data))
        
        # Get dimensions
        width, height = image.size
        
        # OCR text extraction (if available)
        ocr_text = ""
        if TESSERACT_AVAILABLE:
            try:
                ocr_text = pytesseract.image_to_string(image, lang='eng')
                logger.info(f"Extracted {len(ocr_text)} characters from image via OCR")
            except Exception as e:
                logger.warning(f"OCR failed for {filename}: {e}")
        else:
            logger.info("OCR not available - skipping text extraction")
        
        # Detect document types based on content
        documents_detected = []
        if ocr_text:
            ocr_lower = ocr_text.lower()
            
            if any(keyword in ocr_lower for keyword in ['police', 'report', 'incident']):
                documents_detected.append('police_report')
            if any(keyword in ocr_lower for keyword in ['medical', 'hospital', 'doctor']):
                documents_detected.append('medical_record')
            if any(keyword in ocr_lower for keyword in ['invoice', 'receipt', 'bill']):
                documents_detected.append('receipt')
            if any(keyword in ocr_lower for keyword in ['license', 'driving', 'permit']):
                documents_detected.append('license')
            if any(keyword in ocr_lower for keyword in ['insurance', 'policy', 'coverage']):
                documents_detected.append('insurance_document')
        
        # Basic damage/object detection (if OpenCV available)
        has_damage_indicators = False
        if CV2_AVAILABLE:
            try:
                image_array = np.array(image)
                has_damage_indicators = detect_damage_indicators(image_array)
            except Exception as e:
                logger.warning(f"Damage detection failed: {e}")
        
        return {
            "type": "image",
            "filename": filename,
            "dimensions": {"width": width, "height": height},
            "ocr_text": ocr_text,
            "documents_detected": documents_detected,
            "has_damage_indicators": has_damage_indicators,
            "confidence": 0.7 if ocr_text else 0.4
        }
        
    except Exception as e:
        logger.error(f"Image analysis failed for {filename}: {e}")
        return {
            "type": "image",
            "filename": filename,
            "error": str(e),
            "confidence": 0.0
        }


def analyze_pdf(pdf_data: bytes, filename: str) -> Dict[str, Any]:
    """
    Analyze a PDF file: extract text and metadata.
    Works even if PyPDF2 is not available (returns basic metadata).
    
    Args:
        pdf_data: Raw PDF bytes
        filename: Original filename
        
    Returns:
        Dictionary with extracted text and metadata
    """
    if not PDF2_AVAILABLE:
        return {
            "type": "pdf",
            "filename": filename,
            "error": "PyPDF2 not available",
            "confidence": 0.0
        }
    
    try:
        pdf_file = io.BytesIO(pdf_data)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text_parts = []
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text = page.extract_text()
                text_parts.append(text)
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num}: {e}")
        
        full_text = "\n\n".join(text_parts)
        
        # Detect document types
        documents_detected = []
        if full_text:
            text_lower = full_text.lower()
            
            if any(keyword in text_lower for keyword in ['police', 'report', 'incident']):
                documents_detected.append('police_report')
            if any(keyword in text_lower for keyword in ['medical', 'hospital', 'doctor']):
                documents_detected.append('medical_record')
            if any(keyword in text_lower for keyword in ['invoice', 'receipt', 'bill']):
                documents_detected.append('receipt')
            if any(keyword in text_lower for keyword in ['insurance', 'policy', 'coverage']):
                documents_detected.append('insurance_document')
        
        return {
            "type": "pdf",
            "filename": filename,
            "page_count": len(pdf_reader.pages),
            "extracted_text": full_text,
            "documents_detected": documents_detected,
            "confidence": 0.8 if full_text else 0.3
        }
        
    except Exception as e:
        logger.error(f"PDF analysis failed for {filename}: {e}")
        return {
            "type": "pdf",
            "filename": filename,
            "error": str(e),
            "confidence": 0.0
        }


def analyze_video(video_data: bytes, filename: str) -> Dict[str, Any]:
    """
    Analyze a video file: extract frames and perform basic analysis.
    Note: Full video analysis is computationally expensive.
    This extracts key frames and performs basic detection.
    Works even if OpenCV is not available (returns basic metadata).
    
    Args:
        video_data: Raw video bytes
        filename: Original filename
        
    Returns:
        Dictionary with extracted metadata
    """
    if not CV2_AVAILABLE:
        return {
            "type": "video",
            "filename": filename,
            "error": "OpenCV not available",
            "confidence": 0.0
        }
    
    try:
        # Save to temporary file for OpenCV
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(video_data)
            tmp_path = tmp_file.name
        
        try:
            # Open video with OpenCV
            cap = cv2.VideoCapture(tmp_path)
            
            if not cap.isOpened():
                raise ValueError("Could not open video file")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            # Extract key frames (every 30th frame)
            key_frames = []
            frame_num = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_num % 30 == 0:  # Sample every 30 frames
                    # Convert to PIL Image for OCR (if available)
                    if PIL_AVAILABLE and TESSERACT_AVAILABLE:
                        try:
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            pil_image = Image.fromarray(frame_rgb)
                            
                            # Basic OCR on frame
                            ocr_text = pytesseract.image_to_string(pil_image, lang='eng')
                            if ocr_text.strip():
                                key_frames.append({
                                    "frame": frame_num,
                                    "ocr_text": ocr_text[:500]  # Limit text length
                                })
                        except Exception as e:
                            logger.warning(f"OCR on frame {frame_num} failed: {e}")
                
                frame_num += 1
                
                # Limit to first 100 frames for performance
                if frame_num >= 100:
                    break
            
            cap.release()
            
            return {
                "type": "video",
                "filename": filename,
                "duration_seconds": duration,
                "fps": fps,
                "dimensions": {"width": width, "height": height},
                "frame_count": frame_count,
                "key_frames_analyzed": len(key_frames),
                "key_frames": key_frames,
                "confidence": 0.6 if key_frames else 0.3
            }
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
    except Exception as e:
        logger.error(f"Video analysis failed for {filename}: {e}")
        return {
            "type": "video",
            "filename": filename,
            "error": str(e),
            "confidence": 0.0
        }


def detect_damage_indicators(image_array) -> bool:
    """
    Basic damage detection using edge detection and color analysis.
    This is a simplified version - can be enhanced with trained ML models.
    Works only if OpenCV is available.
    
    Args:
        image_array: NumPy array of image
        
    Returns:
        True if damage indicators detected, False otherwise
    """
    if not CV2_AVAILABLE:
        return False
    
    try:
        # Convert to grayscale
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array
        
        # Edge detection (Canny)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # High edge density might indicate damage/cracks
        # This is a heuristic - real implementation would use trained models
        return edge_density > 0.1
        
    except Exception as e:
        logger.warning(f"Damage detection failed: {e}")
        return False


def process_attachments(attachments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process multiple attachments and aggregate results.
    
    Args:
        attachments: List of dicts with 'filename', 'content_type', 'data' (bytes)
        
    Returns:
        Aggregated CV metadata for LLM
    """
    all_documents = []
    all_text = []
    cv_results = []
    
    for attachment in attachments:
        filename = attachment.get("filename", "unknown")
        content_type = attachment.get("content_type", "")
        data = attachment.get("data")
        
        if not data:
            continue
        
        # Route to appropriate analyzer
        if content_type.startswith("image/"):
            result = analyze_image(data, filename)
        elif content_type == "application/pdf":
            result = analyze_pdf(data, filename)
        elif content_type.startswith("video/"):
            result = analyze_video(data, filename)
        else:
            logger.warning(f"Unsupported content type: {content_type}")
            continue
        
        cv_results.append(result)
        
        # Aggregate documents detected
        if "documents_detected" in result:
            all_documents.extend(result["documents_detected"])
        
        # Aggregate text
        if "ocr_text" in result:
            all_text.append(result["ocr_text"])
        if "extracted_text" in result:
            all_text.append(result["extracted_text"])
    
    # Return aggregated metadata
    return {
        "documents_detected": list(set(all_documents)),  # Unique documents
        "extracted_text": "\n\n".join(all_text),
        "attachment_count": len(cv_results),
        "cv_results": cv_results,
        "confidence": max([r.get("confidence", 0) for r in cv_results], default=0.0)
    }
