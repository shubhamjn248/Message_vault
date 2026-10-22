"""Server-side redaction helpers. Redact before a message is persisted."""
import re
import ipaddress

EMAIL_RE = re.compile(r"(?<![\w.+-])[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+(?![\w.-])", re.IGNORECASE)
JWT_RE = re.compile(
    r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+(?![A-Za-z0-9_-])"
)
IPV4_CANDIDATE_RE = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
CARD_CANDIDATE_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")

def _valid_ipv4(value: str) -> bool:
    try:
        ipaddress.IPv4Address(value)
        return True
    except ipaddress.AddressValueError:
        return False

def _luhn_valid(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    if not 13 <= len(digits) <= 19 or len(set(digits)) == 1:
        return False
    total = 0
    parity = len(digits) % 2
    for i, char in enumerate(digits):
        n = int(char)
        if i % 2 == parity:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

def redact_message(message: str) -> str:
    """Mask JWTs, emails, valid IPv4 addresses, and Luhn-valid card candidates."""
    if not isinstance(message, str):
        raise TypeError("message must be a string")
    result = JWT_RE.sub("[REDACTED_JWT]", message)
    result = EMAIL_RE.sub("[REDACTED_EMAIL]", result)
    result = IPV4_CANDIDATE_RE.sub(
        lambda match: "[REDACTED_IPV4]" if _valid_ipv4(match.group(0)) else match.group(0),
        result,
    )
    result = CARD_CANDIDATE_RE.sub(
        lambda match: "[REDACTED_CREDIT_CARD]" if _luhn_valid(match.group(0)) else match.group(0),
        result,
    )
    return result
