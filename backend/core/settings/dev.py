from .base import *

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '*',
]

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

INSTALLED_APPS += [
    'debug_toolbar',
    'django_extensions',
]

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# (Django will create this folder automatically when you run collectstatic)
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'

STATICFILES_DIRS = [
    # BASE_DIR / "apps/frontend/next/src",
    BASE_DIR / 'static',
]

# reCaptcha
SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

# Cros Origin Settings
CORS_ALLOWED_ORIGINS = [
    # 'http://localhost:3000',
    # 'http://127.0.0.1:3000',
]

# Tells WhiteNoise to search for files in your static folders during Dev
# and serve them with the correct headers (ETags).
WHITENOISE_USE_FINDERS = True
