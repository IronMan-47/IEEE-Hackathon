from agent.execution.authorization import auth_service
import pytest
from agent.context.cross_application import ContextSanitizer

def test_sanitizer_removes_passwords():
    payload = {
        "user": "admin",
        "config": 'password: "mySuperSecretPassword123!"',
        "code": "db_password = 'dev_password'"
    }
    sanitized = ContextSanitizer.sanitize(payload)
    
    assert "mySuperSecretPassword123!" not in sanitized["config"]
    assert "REDACTED_PASSWORD" in sanitized["config"]
    assert "dev_password" not in sanitized["code"]
    assert "REDACTED_PASSWORD" in sanitized["code"]
    assert sanitized["user"] == "admin"

def test_sanitizer_removes_bearer_tokens():
    payload = {
        "headers": "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    sanitized = ContextSanitizer.sanitize(payload)
    assert "eyJhbGciOi" not in sanitized["headers"]
    assert "REDACTED_BEARER_TOKEN" in sanitized["headers"]

def test_sanitizer_removes_api_keys():
    payload = {
        "env": "API_KEY='sk-1234567890abcdef'"
    }
    sanitized = ContextSanitizer.sanitize(payload)
    assert "sk-1234567890abcdef" not in sanitized["env"]
    assert "REDACTED_API_KEY" in sanitized["env"]

def test_sanitizer_removes_nested_secrets():
    payload = {
        "nested": {
            "token_list": [
                "some benign string",
                "secret: 'hidden_token'"
            ]
        }
    }
    sanitized = ContextSanitizer.sanitize(payload)
    assert "hidden_token" not in sanitized["nested"]["token_list"][1]
    assert "REDACTED_SECRET" in sanitized["nested"]["token_list"][1]
