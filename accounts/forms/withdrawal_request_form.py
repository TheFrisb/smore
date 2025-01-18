import re

from bech32 import bech32_decode


def is_valid_btc_address(address):
    """
    Validates Bitcoin address for legacy, P2SH, and Bech32 formats.
    """
    # Legacy address validation (P2PKH and P2SH)
    legacy_regex = r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$"
    if re.match(legacy_regex, address):
        return True

    # Bech32 address validation
    try:
        hrp, data = bech32_decode(address)
        if hrp == "bc" and data:
            return True
    except Exception:
        pass

    return False
