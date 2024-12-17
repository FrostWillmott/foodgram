from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .constants import FORBIDDEN_USERNAMES


def forbidden_username_validator(username):
    if username in FORBIDDEN_USERNAMES:
        raise ValidationError(f"Username '{username}' is not allowed.")


def validate_year(value):
    current_year = timezone.now().year
    if value > current_year:
        raise ValidationError(f"Год не может быть больше чем {current_year}.")
