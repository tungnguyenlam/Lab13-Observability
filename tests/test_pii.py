from app.pii import hash_user_id, scrub_text, scrub_value, summarize_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "[REDACTED_EMAIL]" in out


def test_scrub_email_case_insensitive() -> None:
    assert "[REDACTED_EMAIL]" in scrub_text("FOO.BAR+spam@Example.COM")


def test_scrub_phone_vn_variants() -> None:
    for phone in ["+84 90 123 4567", "0901234567", "090.123.4567", "090-123-4567"]:
        assert "[REDACTED_PHONE_VN]" in scrub_text(f"Call me: {phone}")


def test_scrub_credit_card_and_not_cccd() -> None:
    out = scrub_text("card 4111 1111 1111 1111 end")
    assert "[REDACTED_CREDIT_CARD]" in out
    assert "4111" not in out


def test_scrub_cccd() -> None:
    out = scrub_text("CCCD 012345678901 ok")
    assert "[REDACTED_CCCD]" in out


def test_scrub_passport() -> None:
    assert "[REDACTED_PASSPORT]" in scrub_text("passport A1234567")


def test_scrub_jwt() -> None:
    token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abcDEF_123-xyz"
    assert "[REDACTED_JWT]" in scrub_text(f"token={token}")


def test_scrub_api_key() -> None:
    assert "[REDACTED_API_KEY]" in scrub_text("key=sk_live_ABCDEFGHIJKLMNOP1234")


def test_scrub_ipv4() -> None:
    assert "[REDACTED_IPV4]" in scrub_text("client 192.168.1.42 connected")


def test_scrub_address_vn() -> None:
    assert "REDACTED_ADDRESS_VN" in scrub_text("Số nhà 12 đường Láng, Hà Nội")


def test_scrub_text_is_idempotent() -> None:
    once = scrub_text("user@example.com")
    twice = scrub_text(once)
    assert once == twice


def test_scrub_text_non_string_passthrough() -> None:
    assert scrub_text(None) is None
    assert scrub_text(42) == 42


def test_scrub_value_recurses() -> None:
    data = {
        "event": "request_received",
        "payload": {
            "message": "contact student@vinuni.edu.vn",
            "nested": [{"phone": "+84 90 123 4567"}, "ok"],
        },
    }
    out = scrub_value(data)
    assert "[REDACTED_EMAIL]" in out["payload"]["message"]
    assert "[REDACTED_PHONE_VN]" in out["payload"]["nested"][0]["phone"]
    assert out["payload"]["nested"][1] == "ok"


def test_summarize_text_truncates_and_scrubs() -> None:
    raw = "email student@vinuni.edu.vn " * 10
    out = summarize_text(raw, max_len=40)
    assert "student@" not in out
    assert len(out) <= 43  # 40 chars + ellipsis


def test_hash_user_id_stable_and_short() -> None:
    h1 = hash_user_id("u-1")
    h2 = hash_user_id("u-1")
    assert h1 == h2 and len(h1) == 12
    assert hash_user_id("u-1") != hash_user_id("u-2")


def test_hash_user_id_uses_salt(monkeypatch) -> None:
    monkeypatch.delenv("USER_ID_SALT", raising=False)
    plain = hash_user_id("u-1")
    monkeypatch.setenv("USER_ID_SALT", "pepper")
    salted = hash_user_id("u-1")
    assert plain != salted
