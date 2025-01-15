import re

from bech32 import bech32_decode
from django import forms
from django.core.exceptions import ValidationError

from accounts.models import WithdrawalRequest


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


class WithdrawalRequestForm(forms.ModelForm):
    class Meta:
        model = WithdrawalRequest
        fields = ["amount", "payout_destination"]

    def clean_payout_destination(self):
        payout_destination = self.cleaned_data["payout_destination"]
        if not is_valid_btc_address(payout_destination):
            raise ValidationError("Invalid Bitcoin address.")
        return payout_destination
