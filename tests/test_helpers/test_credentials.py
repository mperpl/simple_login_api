import pytest
from fastapi import HTTPException
from app.helpers.credentials import compare_ids, hash_password, verify_password


def test_hash_password():
    password = "my_secure_password"
    hashed = hash_password(password)

    assert hashed != password
    assert len(hashed) > 10
    assert verify_password(password, hashed) is True


def test_verify_password_correct():
    password = "test_password"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    password = "test_password"
    wrong_password = "wrong_password"
    hashed = hash_password(password)
    assert verify_password(wrong_password, hashed) is False


def test_compare_ids_success():
    assert compare_ids(1, 1) is None
    assert compare_ids("uuid-123", "uuid-123") is None


def test_compare_ids_forbidden():
    with pytest.raises(HTTPException) as e:
        compare_ids(1, 2)

    assert e.value.status_code == 403
    assert e.value.detail == "Not authorized"
