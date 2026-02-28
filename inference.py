"""
Inference Engine for PRISM
Provides real-time scam detection predictions
"""

import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from src.utils import (
    detect_language,
    preprocess_text,
    extract_suspicious_keywords,
    extract_urls,
    extract_phone_numbers,
    calculate_risk_score,
    get_risk_level,
    get_language_name
)
import os
try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None


class PrismInference:
    """
    PRISM Inference Engine for Scam Detection
    """
    
    def __init__(self, model_path='models/prism-scam-detector'):
        """
        Initialize the inference engine
        
        Args:
            model_path: Path to trained model directory
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"🔄 Loading PRISM model from {model_path}...")
        
        # Load tokenizer and model
        self.tokenizer = DistilBertTokenizer.from_pretrained(model_path)
        self.model = DistilBertForSequenceClassification.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        
        print(f"✅ Model loaded successfully on {self.device}")
    
    def predict(self, text: str) -> dict:
        """
        Predict if message is scam, suspicious, or safe
        
        Args:
            text: Input message text
            
        Returns:
            Dictionary containing prediction results
        """
        # Detect language
        lang_code = detect_language(text)
        lang_name = get_language_name(lang_code)
        
        # Preprocess text
        cleaned_text = preprocess_text(text)
        
        # Maximize language understanding by translating to English if not English
        text_for_model = cleaned_text
        if lang_code != 'en' and GoogleTranslator:
            try:
                translated = GoogleTranslator(source='auto', target='en').translate(cleaned_text)
                if translated:
                    text_for_model = translated
            except Exception as e:
                print(f"Translation error: {e}")
        
        # Extract features (use translated text for keywords to maximize English pattern matching)
        keywords, keyword_categories = extract_suspicious_keywords(text_for_model)
        urls = extract_urls(text)
        phone_numbers = extract_phone_numbers(text)
        
        # Tokenize for model using translated English semantics
        inputs = self.tokenizer(
            text_for_model,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Get prediction
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
        
        # Get probabilities
        safe_prob = probs[0][0].item()
        scam_prob = probs[0][1].item()
        
        # Calculate risk score
        risk_score = calculate_risk_score(
            prediction_prob=scam_prob,
            keyword_count=len(keywords),
            has_urls=len(urls) > 0,
            has_phone=len(phone_numbers) > 0
        )
        
        # Get risk level
        risk_level = get_risk_level(risk_score)
        
        # Prepare result
        result = {
            'text': text,
            'language': lang_name,
            'language_code': lang_code,
            'prediction': risk_level,
            'risk_score': risk_score,
            'confidence': {
                'safe': round(safe_prob * 100, 2),
                'scam': round(scam_prob * 100, 2)
            },
            'suspicious_keywords': keywords,
            'keyword_categories': keyword_categories,
            'urls_found': urls,
            'phone_numbers_found': phone_numbers,
            'indicators': {
                'has_urgency': 'urgency' in keyword_categories,
                'has_financial_terms': 'financial' in keyword_categories,
                'has_action_required': 'action_required' in keyword_categories,
                'has_threats': 'threats' in keyword_categories,
                'requests_personal_info': 'personal_info' in keyword_categories,
                'contains_urls': len(urls) > 0,
                'contains_phone': len(phone_numbers) > 0
            }
        }
        
        return result
    
    def get_explanation(self, result: dict) -> str:
        """
        Generate human-readable explanation of prediction
        
        Args:
            result: Prediction result dictionary
            
        Returns:
            Explanation string
        """
        explanation = []
        
        if result['prediction'] == 'Scam':
            explanation.append("🚨 HIGH RISK: This message shows strong indicators of a scam.")
        elif result['prediction'] == 'Suspicious':
            explanation.append("⚠️  SUSPICIOUS: This message contains warning signs.")
        else:
            explanation.append("✅ SAFE: This message appears legitimate.")
        
        # Add indicator explanations
        indicators = result['indicators']
        
        if indicators['has_urgency']:
            explanation.append("• Uses urgency tactics to pressure you")
        
        if indicators['has_financial_terms']:
            explanation.append("• Mentions financial rewards or payments")
        
        if indicators['has_action_required']:
            explanation.append("• Demands immediate action (click, verify, update)")
        
        if indicators['has_threats']:
            explanation.append("• Contains threats or legal warnings")
        
        if indicators['requests_personal_info']:
            explanation.append("• Asks for sensitive personal information")
        
        if indicators['contains_urls']:
            explanation.append(f"• Contains {len(result['urls_found'])} suspicious link(s)")
        
        if indicators['contains_phone']:
            explanation.append(f"• Contains {len(result['phone_numbers_found'])} phone number(s)")
        
        return "\n".join(explanation)


def test_inference():
    """Test the inference engine with sample messages"""
    
    # Initialize inference
    inference = PrismInference()
    
    # Test messages
    test_messages = [
        "Hey, want to grab coffee tomorrow?",
        "URGENT! Your bank account will be suspended. Click here to verify immediately.",
        "आपका बैंक खाता ब्लॉक हो जाएगा। तुरंत OTP भेजें।"
    ]
    
    print("\n" + "=" * 80)
    print("🧪 TESTING INFERENCE ENGINE")
    print("=" * 80)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Test {i} ---")
        print(f"Message: {message}")
        
        result = inference.predict(message)
        
        print(f"\nPrediction: {result['prediction']}")
        print(f"Risk Score: {result['risk_score']}/100")
        print(f"Language: {result['language']}")
        print(f"Confidence: Safe={result['confidence']['safe']}%, Scam={result['confidence']['scam']}%")
        
        if result['suspicious_keywords']:
            print(f"Keywords: {', '.join(result['suspicious_keywords'][:5])}")
        
        print(f"\n{inference.get_explanation(result)}")
        print("-" * 80)


if __name__ == "__main__":
    test_inference()
