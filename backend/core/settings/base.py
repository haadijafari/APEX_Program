import os
from pathlib import Path

from django.templatetags.static import static
from django.urls import reverse_lazy
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Secret Key
SECRET_KEY = os.environ.get("SECRET_KEY")
# Debug Status
DEBUG = os.environ.get("DEBUG") == "True"
# User
AUTH_USER_MODEL = "accounts.User"


# Application definition
INSTALLED_APPS = [
    # Django Admin Panel Theme
    "unfold",
    "unfold.contrib.filters",  # Optional: Adds nice sidebar filters
    "unfold.contrib.forms",  # Optional: nicer forms
    "unfold.contrib.import_export",  # Optional: if you use django-import-export
    # Django Apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Project Apps
    "apps.accounts",
    "apps.api",
    "apps.tasks",
    "apps.gate",
    "apps.conquests",
    "apps.inventory",
    "apps.library",
    "apps.profiles",
    "apps.quests",
    # Modules
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "taggit",
    "tinymce",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"


# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True


# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# REST Settings
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Project API",
    "DESCRIPTION": "Project APIs",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # OTHER SETTINGS
}

# Auth Redirects
LOGIN_URL = "login"  # If not logged in, go here
LOGIN_REDIRECT_URL = "gate:index"  # After login, go here (Index Page)
LOGOUT_REDIRECT_URL = "login"  # After logout, go back to login

# Unfold Admin Panel Settings
UNFOLD = {
    "SITE_TITLE": "Apex Program",
    "SITE_HEADER": "Apex Admin",
    "SITE_URL": "/",
    "SITE_ICON": lambda request: static("img/favicon.png"),
    # "DASHBOARD_CALLBACK": "apps.core.views.dashboard_callback",  # render custom charts or stats on the admin homepage
    "SIDEBAR": {
        "show_search": True,  # Search in applications and models names
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Daily Operation",
                "separator": True,
                "items": [
                    {
                        "title": "Gate (Daily View)",
                        "icon": "home",
                        "link": reverse_lazy("admin:gate_dailyentry_changelist"),
                    },
                ],
            },
            {
                "title": "Grimoire (Planning)",
                "separator": True,
                "items": [
                    {
                        "title": "Tasks",
                        "icon": "check_circle",
                        "link": reverse_lazy("admin:tasks_onetimetask_changelist"),
                    },
                    {
                        "title": "Habits",
                        "icon": "edit_calendar",
                        "link": reverse_lazy("admin:tasks_habit_changelist"),
                    },
                    {
                        "title": "Tags",
                        "icon": "label",
                        "link": reverse_lazy("admin:taggit_tag_changelist"),
                    },
                    # If you have a separate model for TaskLog/History, useful to see raw logs
                    # {
                    #     "title": "Completion Logs",
                    #     "icon": "history",
                    #     "link": reverse_lazy("admin:tasks_tasklog_changelist"),
                    # },
                ],
            },
            {
                "title": "Character",
                "separator": True,
                "items": [
                    {
                        "title": "Player Profile",
                        "icon": "face",
                        "link": reverse_lazy("admin:profiles_playerprofile_changelist"),
                    },
                    # {
                    #     "title": "Inventory",
                    #     "icon": "backpack",  # If you have the inventory app
                    #     "link": reverse_lazy("admin:inventory_item_changelist"),
                    # },
                ],
            },
            {
                "title": "System",
                "separator": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "people",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                    },
                    {
                        "title": "Groups",
                        "icon": "lock",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },
}


# TinyMCE Configuration
TINYMCE_DEFAULT_CONFIG = {
    "theme": "silver",
    "height": 300,
    "menubar": True,
    "plugins": "advlist autolink lists link image charmap preview anchor "
    "searchreplace visualblocks code fullscreen insertdatetime media table help wordcount",
    "toolbar": "undo redo | formatselect | "
    "bold italic backcolor | alignleft aligncenter "
    "alignright alignjustify | bullist numlist outdent indent | "
    "removeformat | help",
    # Dark Mode Settings
    "skin": "oxide-dark",
    "content_css": "dark",
}
