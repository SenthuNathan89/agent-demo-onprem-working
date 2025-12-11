import re
from typing import Tuple, List


# Output Guardrail for PII detection and masking
class OutputGuardrails:
    def __init__(self):
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'abn': r'\b\d{2}\s\d{3}\s\d{3}\s\d{3}\b'
        }
        self.secret_patterns = {
            'generic_api_key':r'\b[A-Za-z0-9]{32,}\b',  # Generic API key
            'openai_api_key': r'sk-[A-Za-z0-9]{48}',     # OpenAI style
            'aws_api_key': r'AKIA[0-9A-Z]{16}',       # AWS access key
            'password_field': r'(?i)(?:password|passwd|pwd)[\s:=]+[^\s]+',
            'private_key': r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----',
            'jwt_token': r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+',
            'oauth_token': r'(?i)(?:access_token|bearer)[\s:=]+[A-Za-z0-9\-._~+/]+',
        }
    
    def mask_pii(self, text: str) -> Tuple[str, List[str]]:
        # Mask PII in text and return cleaned/ masked text + detected types
        masked_text = text
        detected_types = []
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                detected_types.append(pii_type)
                # Replace with self-defined mask
                masked_text = re.sub(pattern, f'[{pii_type.upper()}_REDACTED]', masked_text)
        
        return masked_text, detected_types
    
    
    def mask_secret(self, text: str) -> Tuple[str, List[str]]:
        # Mask secret in text and return cleaned/ masked text + detected types
        masked_text = text
        detected_types = []
        
        for secret_type, pattern in self.secret_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                detected_types.append(secret_type)
                # Replace with self-defined mask
                masked_text = re.sub(pattern, f'[{secret_type.upper()}_REDACTED]', masked_text)
        
        return masked_text, detected_types
    
    def toxicity_check(self, text: str) -> bool:
        # Simple toxicity check - returns True if toxic content is found
        toxic_patterns = [
            r'\b(hate|kill|stupid|idiot|dumb)\b',
            r'\b(fuck|shit|bitch|asshole)\b',
        ]
        
        lower_text = text.lower()
        for pattern in toxic_patterns:
            if re.search(pattern, lower_text):
                return True
        return False
    
    def is_safe(self, text: str) -> bool:
        # Check if text contains high-risk secret key and return False if text should be blocked
        has_ssn = bool(re.search(self.pii_patterns['ssn'], text))
        has_cc = bool(re.search(self.pii_patterns['credit_card'], text))
        has_abn = bool(re.search(self.pii_patterns['abn'], text))
        has_api_key = bool(re.search(self.secret_patterns['generic_api_key'], text))

        return not (has_ssn or has_cc or has_abn or has_api_key)
    
