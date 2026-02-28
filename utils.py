"""
Utility functions for PRISM
Handles language detection, text preprocessing, and keyword extraction
"""

import re
from typing import List, Tuple
from langdetect import detect, LangDetectException


# Suspicious keyword patterns for scam detection
SUSPICIOUS_KEYWORDS = {
    'urgency': [
        'urgent', 'immediately', 'now', 'hurry', 'limited time', 'expire',
        'तुरंत', 'जल्दी', 'अभी', 'समाप्त'
    ],
    'financial': [
        'bank', 'account', 'credit card', 'debit card', 'payment', 'refund',
        'winner', 'prize', 'lottery', 'money', 'cash', 'reward',
        'बैंक', 'खाता', 'पैसे', 'रिफंड', 'पुरस्कार', 'लॉटरी'
    ],
    'action_required': [
        'verify', 'confirm', 'update', 'click', 'link', 'activate',
        'suspend', 'blocked', 'locked', 'security',
        'सत्यापित', 'अपडेट', 'क्लिक', 'लिंक', 'ब्लॉक'
    ],
    'threats': [
        'suspended', 'terminated', 'legal', 'police', 'arrest', 'fine',
        'कार्रवाई', 'कानूनी', 'पुलिस', 'जुर्माना'
    ],
    'personal_info': [
        'password', 'pin', 'otp', 'cvv', 'ssn', 'aadhar', 'pan',
        'पासवर्ड', 'पिन', 'ओटीपी', 'आधार'
    ]
}


def detect_language(text: str) -> str:
    """
    Detect the language of input text
    
    Args:
        text: Input text string
        
    Returns:
        Language code (e.g., 'en', 'hi') or 'unknown'
    """
    try:
        lang = detect(text)
        return lang
    except LangDetectException:
        return 'unknown'


def preprocess_text(text: str) -> str:
    """
    Clean and preprocess text for model input
    
    Args:
        text: Raw input text
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.,!?\-\'\"।]', '', text)
    
    return text.strip()


def extract_suspicious_keywords(text: str) -> Tuple[List[str], dict]:
    """
    Extract suspicious keywords from text
    
    Args:
        text: Input text to analyze
        
    Returns:
        Tuple of (list of found keywords, category counts)
    """
    text_lower = text.lower()
    found_keywords = []
    category_counts = {}
    
    for category, keywords in SUSPICIOUS_KEYWORDS.items():
        count = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
                count += 1
        
        if count > 0:
            category_counts[category] = count
    
    return found_keywords, category_counts


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text
    
    Args:
        text: Input text
        
    Returns:
        List of URLs found
    """
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    
    # Also find shortened URLs or suspicious domains
    short_url_pattern = r'(?:bit\.ly|tinyurl|goo\.gl|ow\.ly)/[a-zA-Z0-9]+'
    short_urls = re.findall(short_url_pattern, text, re.IGNORECASE)
    
    return urls + short_urls


def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract phone numbers from text
    
    Args:
        text: Input text
        
    Returns:
        List of phone numbers found
    """
    # Indian phone number patterns
    patterns = [
        r'\+91[-\s]?\d{10}',
        r'\d{10}',
        r'\d{5}[-\s]\d{5}'
    ]
    
    phone_numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        phone_numbers.extend(matches)
    
    return phone_numbers


def calculate_risk_score(
    prediction_prob: float,
    keyword_count: int,
    has_urls: bool,
    has_phone: bool
) -> int:
    """
    Calculate overall risk score (0-100)
    
    Args:
        prediction_prob: Model probability for scam class
        keyword_count: Number of suspicious keywords found
        has_urls: Whether URLs were detected
        has_phone: Whether phone numbers were detected
        
    Returns:
        Risk score from 0-100
    """
    # Base score from model prediction (weighted 70%)
    base_score = prediction_prob * 70
    
    # Keyword penalty (weighted 20%)
    keyword_score = min(keyword_count * 4, 20)
    
    # URL penalty (5%)
    url_score = 5 if has_urls else 0
    
    # Phone number penalty (5%)
    phone_score = 5 if has_phone else 0
    
    total_score = base_score + keyword_score + url_score + phone_score
    
    return int(min(total_score, 100))


def get_risk_level(risk_score: int) -> str:
    """
    Get risk level label from score
    
    Args:
        risk_score: Risk score (0-100)
        
    Returns:
        Risk level: 'Safe', 'Suspicious', or 'Scam'
    """
    if risk_score >= 70:
        return 'Scam'
    elif risk_score >= 40:
        return 'Suspicious'
    else:
        return 'Safe'


def get_language_name(lang_code: str) -> str:
    """
    Convert language code to readable name
    
    Args:
        lang_code: ISO language code
        
    Returns:
        Language name
    """
    lang_map = {
        # Core 22 Scheduled Indian Languages
        'en': 'English', 'hi': 'Hindi', 'mr': 'Marathi', 'ta': 'Tamil', 'te': 'Telugu',
        'bn': 'Bengali', 'gu': 'Gujarati', 'kn': 'Kannada', 'ml': 'Malayalam', 'pa': 'Punjabi',
        'ur': 'Urdu', 'or': 'Odia', 'as': 'Assamese', 'mai': 'Maithili', 'sd': 'Sindhi',
        'ne': 'Nepali', 'sa': 'Sanskrit', 'ks': 'Kashmiri', 'doi': 'Dogri', 'brx': 'Bodo',
        'sat': 'Santali', 'mni': 'Manipuri', 'bho': 'Bhojpuri', 'kok': 'Konkani',

        # Major Foreign Languages (Europe, Asia, Americas, Africa) & Extended
        'zh-cn': 'Chinese (Simplified)', 'zh-tw': 'Chinese (Traditional)', 'es': 'Spanish',
        'fr': 'French', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian',
        'ja': 'Japanese', 'ko': 'Korean', 'ar': 'Arabic', 'th': 'Thai', 'vi': 'Vietnamese',
        'id': 'Indonesian', 'ms': 'Malay', 'tl': 'Tagalog (Filipino)', 'tr': 'Turkish', 'fa': 'Persian',
        'nl': 'Dutch', 'pl': 'Polish', 'sv': 'Swedish', 'da': 'Danish', 'no': 'Norwegian',
        'fi': 'Finnish', 'cs': 'Czech', 'el': 'Greek', 'he': 'Hebrew', 'ro': 'Romanian',
        'hu': 'Hungarian', 'sk': 'Slovak', 'uk': 'Ukrainian', 'bg': 'Bulgarian', 'hr': 'Croatian',
        'sr': 'Serbian', 'lt': 'Lithuanian', 'lv': 'Latvian', 'et': 'Estonian', 'sl': 'Slovenian',
        'sq': 'Albanian', 'af': 'Afrikaans', 'sw': 'Swahili', 'am': 'Amharic', 'yo': 'Yoruba',
        'ig': 'Igbo', 'zu': 'Zulu', 'xh': 'Xhosa', 'my': 'Burmese', 'km': 'Khmer', 'lo': 'Lao',
        'hy': 'Armenian', 'ka': 'Georgian', 'az': 'Azerbaijani', 'uz': 'Uzbek', 'kk': 'Kazakh',
        'ky': 'Kyrgyz', 'mn': 'Mongolian', 'cy': 'Welsh', 'gd': 'Scottish Gaelic', 'ga': 'Irish',
        'is': 'Icelandic', 'mt': 'Maltese', 'ca': 'Catalan', 'mk': 'Macedonian', 'bs': 'Bosnian',
        'be': 'Belarusian', 'tg': 'Tajik', 'tk': 'Turkmen', 'ha': 'Hausa', 'jv': 'Javanese',
        'su': 'Sundanese', 'ku': 'Kurdish', 'sn': 'Shona', 'ny': 'Chichewa', 'sm': 'Samoan',
        'mi': 'Maori', 'haw': 'Hawaiian', 'st': 'Sesotho', 'yi': 'Yiddish', 'rw': 'Kinyarwanda',
        'so': 'Somali', 'mg': 'Malagasy', 'ht': 'Haitian Creole', 'eu': 'Basque', 'gl': 'Galician',
        'la': 'Latin', 'eo': 'Esperanto', 'ceb': 'Cebuano', 'hmn': 'Hmong', 'jw': 'Javanese',
        'unknown': 'Unknown'
    }
    
    return lang_map.get(lang_code, lang_code.upper())
