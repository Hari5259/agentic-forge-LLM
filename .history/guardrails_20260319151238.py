"""
Safety Guardrails Module
Implements rules to prevent agents from performing unauthorized or harmful actions.
Protects sensitive data and enforces security policies.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """Risk levels for content and actions."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


@dataclass
class SafetyCheck:
    """Result of a safety check."""
    is_safe: bool
    risk_level: RiskLevel
    violations: List[str]
    sanitized_content: Optional[str]


class Guardrails:
    """
    Safety guardrails for AI agents.
    Prevents harmful outputs and protects sensitive information.
    """
    
    # Patterns for sensitive data detection
    SENSITIVE_PATTERNS = {
        "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "api_key": r"\b(?:api[_-]?key|apikey|secret|token)[\"']?\s*[:=]\s*[\"']?[\w-]{20,}\b",
        "password": r"\b(?:password|passwd|pwd)[\"']?\s*[:=]\s*[\"'][^\"']+[\"']\b",
    }
    
    # Blocked action types
    BLOCKED_ACTIONS = [
        "execute_system_command",
        "delete_database",
        "access_external_api",
        "send_email_without_approval",
        "modify_system_files",
        "install_software",
        "access_network",
    ]
    
    # Harmful content patterns
    HARMFUL_PATTERNS = [
        r"\b(?:hack|exploit|attack|breach)\b.*\b(?:system|server|database)\b",
        r"\b(?:create|generate|make)\b.*\b(?:malware|virus|ransomware)\b",
        r"\b(?:steal|extract)\b.*\b(?:password|credential|data)\b",
    ]
    
    # Allowed domains for any external operations
    ALLOWED_DOMAINS = []  # Empty = no external domains allowed
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize guardrails.
        
        Args:
            strict_mode: If True, applies more restrictive rules
        """
        self.strict_mode = strict_mode
        self.custom_rules = []
        self.allowed_actions = set()
        self.audit_log = []
    
    def check_input(self, user_input: str) -> SafetyCheck:
        """
        Check user input for safety issues.
        
        Args:
            user_input: The user's message
            
        Returns:
            SafetyCheck result
        """
        violations = []
        risk_level = RiskLevel.SAFE
        
        # Check for harmful intent patterns
        for pattern in self.HARMFUL_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                violations.append(f"Potentially harmful request detected")
                risk_level = RiskLevel.HIGH
        
        # Check for sensitive data in input (user might accidentally paste secrets)
        sensitive_found = self._detect_sensitive_data(user_input)
        if sensitive_found:
            violations.extend([f"Sensitive data detected: {t}" for t in sensitive_found])
            if risk_level != RiskLevel.HIGH:
                risk_level = RiskLevel.MEDIUM
        
        is_safe = risk_level not in [RiskLevel.HIGH, RiskLevel.BLOCKED]
        
        return SafetyCheck(
            is_safe=is_safe,
            risk_level=risk_level,
            violations=violations,
            sanitized_content=self._sanitize_input(user_input) if not is_safe else user_input
        )
    
    def check_output(self, agent_output: str) -> SafetyCheck:
        """
        Check agent output before sending to user.
        
        Args:
            agent_output: The agent's response
            
        Returns:
            SafetyCheck result
        """
        violations = []
        risk_level = RiskLevel.SAFE
        sanitized = agent_output
        
        # Detect and mask sensitive data
        sensitive_found = self._detect_sensitive_data(agent_output)
        if sensitive_found:
            violations.extend([f"Sensitive data in output: {t}" for t in sensitive_found])
            sanitized = self._mask_sensitive_data(agent_output)
            risk_level = RiskLevel.MEDIUM
        
        # Check for harmful content
        for pattern in self.HARMFUL_PATTERNS:
            if re.search(pattern, agent_output, re.IGNORECASE):
                violations.append("Harmful content in output")
                risk_level = RiskLevel.BLOCKED
                sanitized = "[Content blocked for safety reasons]"
                break
        
        is_safe = risk_level not in [RiskLevel.BLOCKED]
        
        return SafetyCheck(
            is_safe=is_safe,
            risk_level=risk_level,
            violations=violations,
            sanitized_content=sanitized
        )
    
    def check_action(self, action_type: str, action_params: Dict) -> SafetyCheck:
        """
        Check if an action is allowed.
        
        Args:
            action_type: Type of action to perform
            action_params: Parameters for the action
            
        Returns:
            SafetyCheck result
        """
        violations = []
        risk_level = RiskLevel.SAFE
        
        # Check if action is explicitly blocked
        if action_type in self.BLOCKED_ACTIONS:
            if action_type not in self.allowed_actions:
                violations.append(f"Action '{action_type}' is not allowed")
                risk_level = RiskLevel.BLOCKED
        
        # Check for external URL access
        if "url" in action_params or "endpoint" in action_params:
            url = action_params.get("url") or action_params.get("endpoint", "")
            if not self._is_allowed_url(url):
                violations.append(f"External URL access not allowed: {url}")
                risk_level = RiskLevel.BLOCKED
        
        # Check for file system access
        if "file_path" in action_params or "path" in action_params:
            path = action_params.get("file_path") or action_params.get("path", "")
            if not self._is_safe_path(path):
                violations.append(f"Unsafe file path: {path}")
                risk_level = RiskLevel.BLOCKED
        
        # Log the action check
        self._log_action_check(action_type, action_params, risk_level)
        
        is_safe = risk_level not in [RiskLevel.BLOCKED]
        
        return SafetyCheck(
            is_safe=is_safe,
            risk_level=risk_level,
            violations=violations,
            sanitized_content=None
        )
    
    def _detect_sensitive_data(self, text: str) -> List[str]:
        """Detect types of sensitive data in text."""
        found = []
        for data_type, pattern in self.SENSITIVE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.append(data_type)
        return found
    
    def _mask_sensitive_data(self, text: str) -> str:
        """Mask sensitive data in text."""
        masked = text
        
        # Mask each type of sensitive data
        for data_type, pattern in self.SENSITIVE_PATTERNS.items():
            if data_type == "email":
                # Partially mask emails
                masked = re.sub(
                    pattern,
                    lambda m: m.group(0)[:3] + "***@" + m.group(0).split("@")[1][:3] + "***",
                    masked, 
                    flags=re.IGNORECASE
                )
            elif data_type in ["credit_card", "ssn", "phone"]:
                # Replace with asterisks
                masked = re.sub(
                    pattern,
                    lambda m: "*" * len(m.group(0)),
                    masked
                )
            elif data_type in ["api_key", "password"]:
                # Replace value only
                masked = re.sub(
                    pattern,
                    "[REDACTED]",
                    masked,
                    flags=re.IGNORECASE
                )
        
        return masked
    
    def _sanitize_input(self, text: str) -> str:
        """Sanitize user input."""
        # Remove potential injection patterns
        sanitized = text
        
        # Remove script-like patterns
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove SQL injection patterns
        sanitized = re.sub(r';\s*(?:DROP|DELETE|UPDATE|INSERT)', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def _is_allowed_url(self, url: str) -> bool:
        """Check if URL is in allowed domains."""
        if not url:
            return True
        
        if not self.ALLOWED_DOMAINS:
            return False  # No external URLs allowed by default
        
        for domain in self.ALLOWED_DOMAINS:
            if domain in url:
                return True
        
        return False
    
    def _is_safe_path(self, path: str) -> bool:
        """Check if file path is safe."""
        if not path:
            return True
        
        # Block access to sensitive directories
        unsafe_patterns = [
            r"\.\.[\\/]",  # Path traversal
            r"[\\/]etc[\\/]",  # Linux system
            r"[\\/]windows[\\/]system",  # Windows system
            r"[\\/]\.ssh[\\/]",  # SSH keys
            r"[\\/]\.env",  # Environment files
        ]
        
        for pattern in unsafe_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return False
        
        return True
    
    def _log_action_check(self, action_type: str, params: Dict, risk_level: RiskLevel):
        """Log an action check for audit purposes."""
        self.audit_log.append({
            "action_type": action_type,
            "params_summary": str(params)[:100],
            "risk_level": risk_level.value
        })
    
    def add_allowed_action(self, action_type: str):
        """Add an action to the allowed list."""
        self.allowed_actions.add(action_type)
    
    def add_custom_rule(self, rule_name: str, pattern: str, risk_level: RiskLevel):
        """Add a custom safety rule."""
        self.custom_rules.append({
            "name": rule_name,
            "pattern": pattern,
            "risk_level": risk_level
        })
    
    def get_audit_log(self) -> List[Dict]:
        """Get the audit log."""
        return self.audit_log.copy()
    
    def clear_audit_log(self):
        """Clear the audit log."""
        self.audit_log = []


def create_safe_prompt(base_prompt: str) -> str:
    """
    Add safety instructions to a prompt.
    
    Args:
        base_prompt: The original prompt
        
    Returns:
        Prompt with safety instructions
    """
    safety_prefix = """
IMPORTANT SAFETY GUIDELINES:
- Never reveal sensitive personal information (SSN, credit cards, passwords)
- Never provide instructions for illegal or harmful activities
- Never generate malicious code or exploits
- Always be helpful, harmless, and honest
- If unsure about safety, err on the side of caution

"""
    return safety_prefix + base_prompt
