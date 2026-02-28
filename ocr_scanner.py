"""
OCR Module for PRISM
Extract text from screenshots and images
"""

from PIL import Image
import pytesseract
import io
import os
import re

# Configure Tesseract path (Windows default)
# If installed elsewhere, update this path
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def preprocess_image(image):
    """
    Preprocess image for better OCR results
    
    Args:
        image: PIL Image object
        
    Returns:
        Preprocessed PIL Image
    """
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Convert to grayscale for better OCR
    image = image.convert('L')
    
    # Increase contrast (optional enhancement)
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    return image


def extract_text_from_image(image_data, preprocess=True):
    """
    Extract text from image using OCR
    
    Args:
        image_data: Image file data (bytes) or PIL Image object
        preprocess: Whether to preprocess image for better results
        
    Returns:
        Dictionary with extracted text and metadata
    """
    try:
        # Load image
        if isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
        elif isinstance(image_data, Image.Image):
            image = image_data
        else:
            return {'error': 'Invalid image data', 'text': ''}
        
        # Store original size
        original_size = image.size
        
        # Preprocess if requested
        if preprocess:
            image = preprocess_image(image)
        
        # Extract text using Tesseract
        # Using English for now (add more languages after installing language packs)
        extracted_text = pytesseract.image_to_string(
            image,
            lang='eng',  # English only for now
            config='--psm 6'  # Assume uniform block of text
        )
        
        # Clean up extracted text
        extracted_text = extracted_text.strip()
        
        # Get detailed OCR data
        ocr_data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            lang='eng'  # English only
        )
        
        # Calculate confidence score
        confidences = [int(conf) for conf in ocr_data['conf'] if conf != '-1']
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Count words detected
        words_detected = len([w for w in ocr_data['text'] if w.strip()])
        
        return {
            'text': extracted_text,
            'success': True,
            'metadata': {
                'image_size': original_size,
                'words_detected': words_detected,
                'average_confidence': round(avg_confidence, 2),
                'languages_checked': ['English']  # Add more after installing language data
            }
        }
    
    except pytesseract.TesseractNotFoundError:
        return {
            'error': 'Tesseract OCR not installed. Please install Tesseract-OCR.',
            'text': '',
            'success': False,
            'installation_guide': 'Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki'
        }
    
    except Exception as e:
        return {
            'error': f'OCR failed: {str(e)}',
            'text': '',
            'success': False
        }


def extract_text_from_file(file_path, preprocess=True):
    """
    Extract text from image file
    
    Args:
        file_path: Path to image file
        preprocess: Whether to preprocess image
        
    Returns:
        Dictionary with extracted text and metadata
    """
    try:
        with Image.open(file_path) as image:
            return extract_text_from_image(image, preprocess)
    except Exception as e:
        return {
            'error': f'Failed to read image file: {str(e)}',
            'text': '',
            'success': False
        }


def is_valid_image(file_data):
    """
    Check if file data is a valid image
    
    Args:
        file_data: File data (bytes)
        
    Returns:
        Boolean indicating if valid image
    """
    try:
        image = Image.open(io.BytesIO(file_data))
        image.verify()
        return True
    except Exception:
        return False


def get_image_info(file_data):
    """
    Get basic information about an image
    
    Args:
        file_data: Image file data (bytes)
        
    Returns:
        Dictionary with image information
    """
    try:
        image = Image.open(io.BytesIO(file_data))
        
        return {
            'format': image.format,
            'mode': image.mode,
            'size': image.size,
            'width': image.size[0],
            'height': image.size[1],
            'is_valid': True
        }
    except Exception as e:
        return {
            'error': str(e),
            'is_valid': False
        }


# Test function
if __name__ == "__main__":
    print("\n📸 OCR Module Test\n")
    print("Note: This module requires Tesseract-OCR to be installed.")
    print("Download from: https://github.com/UB-Mannheim/tesseract/wiki\n")
    
    # Create a test image with text
    from PIL import ImageDraw, ImageFont
    
    # Create a simple test image
    test_image = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(test_image)
    
    # Add text
    text = "URGENT! Your account will be suspended.\nClick here to verify now!"
    draw.text((20, 50), text, fill='black')
    
    print("Testing OCR on generated image...")
    result = extract_text_from_image(test_image)
    
    if result['success']:
        print(f"✅ OCR Successful!")
        print(f"Extracted Text: {result['text'][:100]}...")
        print(f"Words Detected: {result['metadata']['words_detected']}")
        print(f"Confidence: {result['metadata']['average_confidence']}%")
    else:
        print(f"❌ OCR Failed: {result.get('error', 'Unknown error')}")
        if 'installation_guide' in result:
            print(f"📥 {result['installation_guide']}")
