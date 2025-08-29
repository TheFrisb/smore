# utils/apple.py
import time

import jwt
from django.conf import settings


def generate_apple_client_secret() -> str:
    """
    Generates an Apple client secret JWT for Sign in with Apple.
    """
    # Path to your .p8 private key
    key_path = settings.APPLE_SIGN_IN_KEY_PATH

    with open(key_path, "r") as f:
        private_key = f.read()

    team_id = settings.APPLE_TEAM_ID
    client_id = settings.APPLE_CLIENT_ID
    key_id = settings.APPLE_KEY_ID

    headers = {"kid": key_id, "alg": "ES256"}

    payload = {
        "iss": team_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400 * 180,
        "aud": "https://appleid.apple.com",
        "sub": client_id,
    }

    client_secret = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)

    if isinstance(client_secret, bytes):
        client_secret = client_secret.decode("utf-8")

    return client_secret
