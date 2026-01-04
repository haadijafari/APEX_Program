from unfold.forms import UserChangeForm, UserCreationForm

from apps.accounts.models import User


class CustomUserCreationForm(UserCreationForm):
    """
    Used by the Admin Panel.
    Keeps default behavior (including usable_password) so Admin doesn't crash.
    """

    class Meta:
        model = User
        fields = ("username", "email")


class PublicUserCreationForm(UserCreationForm):
    """
    Used by the Register View.
    Removes the admin-only 'usable_password' field and adds styling.
    """

    usable_password = None

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
        )  # Add your custom fields here

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Iterate over all fields (including inherited password fields)
        for field_name, field in self.fields.items():
            # Add Bootstrap class
            field.widget.attrs.update(
                {
                    "class": "form-control",
                    "placeholder": field.label,  # Modern look: placeholder inside input
                }
            )

            # Add specific classes for email/password if needed
            if field_name == "email":
                field.widget.attrs.update({"class": "form-control email-field"})


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"
