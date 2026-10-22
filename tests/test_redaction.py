from app.redaction import redact_message

def test_redacts_all_supported_types():
    message = (
        "email jane.doe@example.com; ip 192.168.1.10; "
        "card 4111 1111 1111 1111; "
        "jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTYifQ.signature"
    )
    result = redact_message(message)
    assert "[REDACTED_EMAIL]" in result
    assert "[REDACTED_IPV4]" in result
    assert "[REDACTED_CREDIT_CARD]" in result
    assert "[REDACTED_JWT]" in result
    for original in ("jane.doe@example.com", "192.168.1.10", "4111 1111 1111 1111", "eyJhbGciOiJIUzI1NiJ9"):
        assert original not in result

def test_multiple_occurrences_are_redacted():
    result = redact_message("a@b.com and c@d.org")
    assert result.count("[REDACTED_EMAIL]") == 2

def test_invalid_ipv4_is_not_redacted_as_valid_ip():
    assert "999.999.999.999" in redact_message("bad IP 999.999.999.999")

def test_non_luhn_card_candidate_is_not_redacted():
    assert "4111111111111112" in redact_message("number 4111111111111112")
