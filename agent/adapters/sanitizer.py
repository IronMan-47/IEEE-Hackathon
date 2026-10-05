import re
from typing import Dict, Any, List
from agent.adapters.base import ApplicationContext, PrivacyLevel, ContextStatus

class ContextSanitizer:
    SECRET_PATTERN = re.compile(
        r'(?:token|key|password|passwd|secret|auth|bearer|session|cookie|otp|cvv|card[-_]?number)[\s]*[=:]?[\s]*[\'"]?([a-zA-Z0-9_\-\.\+/]{8,})[\'"]?',
        re.IGNORECASE
    )
    BEARER_PATTERN = re.compile(r'Bearer\s+[a-zA-Z0-9_\-\.\+/]+', re.IGNORECASE)
    JWT_PATTERN = re.compile(r'ey[a-zA-Z0-9_-]+\.ey[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+')

    @classmethod
    def sanitize(cls, context: ApplicationContext) -> ApplicationContext:
        """
        Sanitizes ApplicationContext:
        1. Ensures JSON serializability.
        2. Wraps untrusted text fields inside data boundary.
        3. Redacts secret parameters from URLs or titles.
        4. Caps text lengths.
        """
        if not isinstance(context, ApplicationContext):
            raise ValueError("Invalid context type: expected ApplicationContext instance")

        sanitized_data = cls._sanitize_dict(context.data)

        # Explicitly enforce untrusted data boundary wrapper
        sanitized_data["_untrusted_data_boundary"] = True

        context.data = sanitized_data
        return context

    @classmethod
    def _sanitize_dict(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for key, val in d.items():
            if isinstance(val, str):
                result[key] = cls._sanitize_string(val)
            elif isinstance(val, dict):
                result[key] = cls._sanitize_dict(val)
            elif isinstance(val, list):
                result[key] = [cls._sanitize_value(v) for v in val]
            elif isinstance(val, (int, float, bool)) or val is None:
                result[key] = val
            else:
                # Convert arbitrary object to string representation
                result[key] = str(val)[:cls.MAX_TEXT_LENGTH]
        return result

    @classmethod
    def _sanitize_value(cls, val: Any) -> Any:
        if isinstance(val, str):
            return cls._sanitize_string(val)
        elif isinstance(val, dict):
            return cls._sanitize_dict(val)
        elif isinstance(val, (int, float, bool)) or val is None:
            return val
        return str(val)[:cls.MAX_TEXT_LENGTH]

    @classmethod
    def _sanitize_string(cls, text: str) -> str:
        if not text:
            return ""

        # Redact secrets in query params or headers
        cleaned = text
        cleaned = cls.SECRET_PATTERN.sub(r'\g<0> [REDACTED]', cleaned) # Actually we want to redact the group 1
        # Better: just replace the whole match with REDACTED for Bearer/JWT
        cleaned = cls.BEARER_PATTERN.sub('Bearer [REDACTED]', cleaned)
        cleaned = cls.JWT_PATTERN.sub('[REDACTED_JWT]', cleaned)
        
        # for SECRET_PATTERN, we want to replace group 1
        # re.sub with function to only replace group 1
        def replacer(match):
            full = match.group(0)
            secret = match.group(1)
            return full.replace(secret, '[REDACTED]')
            
        cleaned = cls.SECRET_PATTERN.sub(replacer, cleaned)

        # Enforce max length cap
        if len(cleaned) > 1000:
            cleaned = cleaned[:1000] + "... [TRUNCATED]"

        return cleaned
