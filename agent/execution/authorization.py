import hmac
import hashlib
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import secrets

class AuthorizationService:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AuthorizationService, cls).__new__(cls)
            cls._instance._secret = secrets.token_bytes(32)
            cls._consumed_tokens = set()  # In a real app this would be in SQLite
        return cls._instance
    
    def __init__(self):
        pass
        
    def generate_token(self, proposal: Any) -> Dict[str, Any]:
        token_id = uuid.uuid4().hex
        issued_at = datetime.now(timezone.utc).isoformat()
        expires_at = proposal.expires_at.isoformat() if hasattr(proposal.expires_at, 'isoformat') else proposal.expires_at
        
        payload = {
            "token_id": token_id,
            "proposal_id": proposal.proposal_id,
            "domain": proposal.domain,
            "base_context_id": proposal.base_context_id,
            "base_context_hash": proposal.base_context_hash,
            "base_revision": proposal.base_revision,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "single_use": True
        }
        
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(self._secret, payload_str.encode('utf-8'), hashlib.sha256).hexdigest()
        
        payload["signature"] = signature
        return payload

    def verify_token(self, token: Dict[str, Any], request: Any) -> bool:
        if not isinstance(token, dict):
            return False
            
        token_id = token.get("token_id")
        if not token_id or token_id in self._consumed_tokens:
            return False
            
        # Verify signature
        provided_signature = token.get("signature")
        if not provided_signature:
            return False
            
        payload = token.copy()
        del payload["signature"]
        payload_str = json.dumps(payload, sort_keys=True)
        expected_signature = hmac.new(self._secret, payload_str.encode('utf-8'), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(provided_signature, expected_signature):
            return False
            
        # Verify bindings
        if token.get("proposal_id") != request.proposal_id:
            return False
        if token.get("base_context_id") != request.base_context_id:
            return False
        if token.get("base_context_hash") != request.base_context_hash:
            return False
        if token.get("base_revision") != request.base_revision:
            return False
            
        # Verify expiration
        try:
            expires_at = datetime.fromisoformat(token.get("expires_at", ""))
            if datetime.now(timezone.utc) > expires_at:
                return False
        except (ValueError, TypeError):
            return False
            
        return True

    def consume_token(self, token_id: str) -> bool:
        if token_id in self._consumed_tokens:
            return False
        self._consumed_tokens.add(token_id)
        return True

auth_service = AuthorizationService()
