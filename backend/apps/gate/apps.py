from django.apps import AppConfig


class GateConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.gate"

    def ready(self):
        import apps.gate.signals
