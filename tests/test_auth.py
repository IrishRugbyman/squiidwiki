"""Tests for Phase 4 auth: argon2 hashing + access/refresh token pair."""
from __future__ import annotations

from datetime import timedelta

import pytest
from jose import JWTError, jwt

from backend.auth.auth_utils import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)


# ─── Password hashing (argon2) ────────────────────────────────────────────────


class TestPasswordHashing:
    def test_hash_and_verify(self):
        hashed = get_password_hash("correct_horse_battery")
        assert verify_password("correct_horse_battery", hashed)

    def test_wrong_password_fails(self):
        hashed = get_password_hash("correct_password")
        assert not verify_password("wrong_password", hashed)

    def test_empty_password_fails(self):
        hashed = get_password_hash("some_password")
        assert not verify_password("", hashed)

    def test_hashes_differ_per_call(self):
        h1 = get_password_hash("same")
        h2 = get_password_hash("same")
        assert h1 != h2  # argon2 uses random salt


# ─── Access token ─────────────────────────────────────────────────────────────


class TestAccessToken:
    def test_contains_sub(self):
        token = create_access_token({"sub": "alice"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "alice"

    def test_typ_is_access(self):
        token = create_access_token({"sub": "alice"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["typ"] == "access"

    def test_expired_token_raises(self):
        token = create_access_token({"sub": "alice"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(JWTError):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    def test_custom_expiry(self):
        token = create_access_token({"sub": "alice"}, expires_delta=timedelta(minutes=5))
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "alice"


# ─── Refresh token ────────────────────────────────────────────────────────────


class TestRefreshToken:
    def test_contains_sub(self):
        token = create_refresh_token({"sub": "bob"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "bob"

    def test_typ_is_refresh(self):
        token = create_refresh_token({"sub": "bob"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["typ"] == "refresh"

    def test_typ_differs_from_access(self):
        access = create_access_token({"sub": "bob"})
        refresh = create_refresh_token({"sub": "bob"})
        access_payload = jwt.decode(access, SECRET_KEY, algorithms=[ALGORITHM])
        refresh_payload = jwt.decode(refresh, SECRET_KEY, algorithms=[ALGORITHM])
        assert access_payload["typ"] != refresh_payload["typ"]

    def test_refresh_longer_lived_than_access(self):
        access = create_access_token({"sub": "bob"})
        refresh = create_refresh_token({"sub": "bob"})
        a = jwt.decode(access, SECRET_KEY, algorithms=[ALGORITHM])
        r = jwt.decode(refresh, SECRET_KEY, algorithms=[ALGORITHM])
        assert r["exp"] > a["exp"]


# ─── Token type enforcement ───────────────────────────────────────────────────


class TestTokenTypeEnforcement:
    """Middleware rejects non-access tokens; refresh endpoint rejects non-refresh tokens."""

    def test_refresh_token_fails_access_typ_check(self):
        token = create_refresh_token({"sub": "carol"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Simulates what auth_middleware does
        assert payload.get("typ") != "access"

    def test_access_token_fails_refresh_typ_check(self):
        token = create_access_token({"sub": "carol"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Simulates what /refresh endpoint does
        assert payload.get("typ") != "refresh"

    def test_wrong_secret_raises(self):
        token = create_access_token({"sub": "eve"})
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong_secret", algorithms=[ALGORITHM])
