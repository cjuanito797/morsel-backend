import phonenumbers

from phonenumbers.phonenumberutil import NumberParseException

def sanitize_phone_number(raw_phone_number, region='US'):
    try:
        parsed = phonenumbers.parse(raw_phone_number, region)
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except NumberParseException:
        return None