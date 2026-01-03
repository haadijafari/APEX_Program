from django.contrib import admin

from apps.profiles.models import PlayerAttribute


class PlayerAttributeInline(admin.TabularInline):
    """Shows the dynamic list of stats (Strength, Python, etc.)"""

    model = PlayerAttribute
    extra = 1  # Allows adding 1 new stat easily
    verbose_name = "Attribute"
    verbose_name_plural = "Player Attributes (Stats)"
