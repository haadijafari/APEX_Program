from django.contrib.auth.forms import UserCreationForm

from apps.accounts.models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        # Add 'email' or other fields here if you want them on registration
        fields = ("username", "email")
