import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app import keys
from app.config import PlatformConfig, settings

TEST_ISSUER = "https://canvas.test.instructure.com"
TEST_CLIENT_ID = "10000000000001"
TEST_DEPLOYMENT_ID = "1:abc123"
TEST_KID = "test-platform-key-1"


def _generate_rsa_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_key, public_key, private_pem, public_pem


@pytest.fixture
def tool_keys():
    _, _, private_pem, public_pem = _generate_rsa_keypair()
    return {"private_pem": private_pem, "public_pem": public_pem}


@pytest.fixture
def platform_keys():
    private_key, public_key, private_pem, public_pem = _generate_rsa_keypair()
    jwk = keys.json_web_key_from_public_key(public_key)
    jwk["kid"] = TEST_KID
    jwk["use"] = "sig"
    jwk["alg"] = "RS256"
    return {
        "private_key": private_key,
        "private_pem": private_pem,
        "public_pem": public_pem,
        "jwks": {"keys": [jwk]},
    }


@pytest.fixture
def test_platform():
    platform = PlatformConfig(
        issuer=TEST_ISSUER,
        client_id=TEST_CLIENT_ID,
        deployment_ids=[TEST_DEPLOYMENT_ID],
        auth_login_url="https://canvas.test.instructure.com/api/lti/authorize_redirect",
        auth_token_url="https://canvas.test.instructure.com/login/oauth2/token",
        key_set_url="https://canvas.test.instructure.com/api/lti/security/jwks",
    )
    settings.platforms[platform.key] = platform
    yield platform
    settings.platforms.pop(platform.key, None)


@pytest.fixture(autouse=True)
def _reset_jwks_cache():
    keys._jwks_cache.clear()
    yield
    keys._jwks_cache.clear()


@pytest.fixture(autouse=True)
def _configure_tool_keys(tool_keys, monkeypatch):
    monkeypatch.setattr(settings, "tool_private_key_pem", tool_keys["private_pem"])
    monkeypatch.setattr(settings, "tool_public_key_pem", tool_keys["public_pem"])
