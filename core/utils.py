"""
Core utility functions for input validation and sanitization.
Provides security functions to prevent XSS attacks and validate user input.
"""
import re
import html
from typing import Optional


def sanitize_input(text: str) -> str:
    """
    Sanitize text input to prevent XSS attacks.
    
    - Strips HTML tags
    - Escapes special characters
    - Removes script content
    
    Args:
        text: Input string to sanitize
        
    Returns:
        Sanitized string safe for storage and display
    """
    if not text:
        return text
    
    # Remove script tags and their content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove event handler attributes (onclick, onload, etc.)
    text = re.sub(r'\s*on\w+\s*=\s*["\']?[^"\']*["\']?', '', text, flags=re.IGNORECASE)
    
    # Remove javascript: protocol in URLs
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    # Strip all HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Escape special HTML characters
    text = html.escape(text)
    
    return text.strip()


def validate_email_format(email: str) -> bool:
    """
    Validate email format according to RFC 5322 standard.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    if not email or len(email) > 254:
        return False
    
    # RFC 5322 compliant email regex pattern
    # Simplified but covers most common cases
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Additional validation rules
    if email.count('@') != 1:
        return False
    
    local_part, domain = email.rsplit('@', 1)
    
    # Local part validation
    if not local_part or len(local_part) > 64:
        return False
    
    # Domain validation
    if not domain or len(domain) > 255:
        return False
    
    # Check for consecutive dots
    if '..' in email:
        return False
    
    # Check if starts or ends with dot
    if local_part.startswith('.') or local_part.endswith('.'):
        return False
    
    return bool(re.match(pattern, email))


def validate_phone_format(phone: str) -> bool:
    """
    Validate phone number format.
    
    Accepts:
    - Digits (0-9)
    - Spaces
    - Hyphens (-)
    - Parentheses ()
    - Plus symbol (+)
    
    Length: minimum 7 characters, maximum 20 characters
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone format is valid, False otherwise
    """
    if not phone:
        return False
    
    # Check length constraints
    if len(phone) < 7 or len(phone) > 20:
        return False
    
    # Pattern: only digits, spaces, hyphens, parentheses, and plus symbol
    pattern = r'^[\d\s\-\(\)\+]+$'
    
    if not re.match(pattern, phone):
        return False
    
    # Ensure at least 7 digits are present (ignoring formatting characters)
    digits_only = re.sub(r'[^\d]', '', phone)
    if len(digits_only) < 7:
        return False
    
    return True


def validate_company_name(name: str) -> bool:
    """
    Validate company name length.
    
    Args:
        name: Company name to validate
        
    Returns:
        True if name length is valid (2-200 characters), False otherwise
    """
    if not name:
        return False
    
    name = name.strip()
    return 2 <= len(name) <= 200


def validate_contact_name(name: str) -> bool:
    """
    Validate contact name length.
    
    Args:
        name: Contact name to validate
        
    Returns:
        True if name length is valid (2-150 characters), False otherwise
    """
    if not name:
        return False
    
    name = name.strip()
    return 2 <= len(name) <= 150


def get_client_ip(request) -> Optional[str]:
    """
    Extract client IP address from request.
    Handles proxy headers (X-Forwarded-For).
    
    Args:
        request: Django request object
        
    Returns:
        IP address string or None
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
