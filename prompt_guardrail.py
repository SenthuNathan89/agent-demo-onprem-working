import re
from typing import List, Tuple, Dict

class InputGuardrails:
    def __init__(self):
        # Define harmful patterns
        self.harmful_patterns = [
            r'\b(kill|murder|harm|attack)\s+(someone|people|person)',
            r'\b(how to|guide to)\s+(hack|exploit|break into)',
            r'\b(create|make|build)\s+(bomb|weapon|explosive)',
            r'\b(steal|fraud|scam)\s+',
        ]
        
        # PII patterns
        self.pii_patterns = {
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        }
        
        # Injection patterns
        self.injection_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',  # events like onclick=
            r';\s*DROP\s+TABLE',  # SQL injection
            r'UNION\s+SELECT',
        ]
        
        self.max_length = 5000
        self.max_repeated_chars = 50
    
    def check_all(self, user_input: str) -> Tuple[bool, List[Dict]]:
        # Run all guardrail checks and return overall pass/fail plus details
        results = []
        results.append(self.check_length(user_input))
        results.append(self.check_harmful_content(user_input))
        results.append(self.check_pii(user_input))
        results.append(self.check_injection(user_input))
        results.append(self.check_repetition(user_input))
        overall_pass = all(r['passed'] for r in results)
        
        return overall_pass, results
    
    def check_length(self, user_input: str) -> Dict:
        if len(user_input) == 0:
            return {
                'passed': False, 'cause':"Input is empty", 'risk_level':"low"
            }
        
        if len(user_input) > self.max_length:
            return {
                "passed":False, 'cause':f"Input exceeds maximum length of {self.max_length} characters", 'risk_level':"moderate"
            }
        
        return {"passed":True, "cause":"Length check passed", 'risk_level':"none"}
    
    def check_harmful_content(self, user_input: str) -> Dict:
        lower_input = user_input.lower()
        
        for pattern in self.harmful_patterns:
            if re.search(pattern, lower_input, re.IGNORECASE):
                return {
                    'passed':False, 'cause':f"Detected harmful content pattern: {pattern}", 'risk_level':"high"
                }
        
        return {'passed':True, 'cause':"No harmful content detected", 'risk_level':"none"}
    
    def check_pii(self, user_input: str) -> Dict:
        detected_pii = []
        
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, user_input):
                detected_pii.append(pii_type)
        
        if detected_pii:
            return {
                'passed':False, 'cause':f"Detected PII: {', '.join(detected_pii)}", 'risk_level':"high"
            }
        
        return {'passed':True, 'cause':"No PII detected", 'risk_level':"none"}
    
    def check_injection(self, user_input: str) -> Dict:
        for pattern in self.injection_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return {
                    'passed':False, 'cause':"Detected potential injection attempt", 'risk_level':"high"
                }
        
        return {'passed':True, 'cause':"No injection patterns detected", 'risk_level':"none"}
    
    def check_repetition(self, user_input: str) -> Dict:
        for i in range(len(user_input) - self.max_repeated_chars):
            window = user_input[i:i + self.max_repeated_chars]
            if len(set(window)) == 1:
                return {
                    "passed":False, 'cause':"Excessive character repetition detected", 'risk_level':"medium"
                }
        
        return {'passed':True, 'cause':"No excessive repetition detected", 'risk_level':"none"}
    
    def sanitize_input(self, user_input: str) -> str:
        # Basic sanitization: remove null bytes, excessive whitespace
        sanitized = user_input.replace('\x00', '')
        sanitized = re.sub(r'\s+', ' ', sanitized)
        sanitized = sanitized.strip()
        
        return sanitized



        
    
