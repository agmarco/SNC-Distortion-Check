import re

from django.core.exceptions import ValidationError


def validate_phone(phone):
    phone_cleaned = re.sub(r'[^\d+x]', '', phone)
    if not re.match(r'^\+?1?\d{9,15}(x\d+)?$', phone_cleaned):
        raise ValidationError("Please enter a valid phone number.")
