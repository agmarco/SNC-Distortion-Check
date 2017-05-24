import re

from django.core.exceptions import ValidationError, ObjectDoesNotExist

from server.common.models import Phantom


def validate_phone(phone):
    phone_cleaned = re.sub(r'[^\d+x]', '', phone)
    if not re.match(r'^\+?1?\d{9,15}(x\d+)?$', phone_cleaned):
        raise ValidationError("Please enter a valid phone number.")


def validate_phantom_serial_number(serial_number):
    try:
        phantom = Phantom.objects.get(serial_number=serial_number)
    except ObjectDoesNotExist:
        raise ValidationError("""That phantom does not exist in our database. If you believe this is a mistake, please
                              contact CIRS support.""")
    if phantom.institution is not None:
        raise ValidationError("""That phantom is already in use. If you believe this is a mistake, please contact CIRS
                              support.""")
