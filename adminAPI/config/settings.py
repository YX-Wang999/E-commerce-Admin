"""
Django settings for config project.
"""

import os
from datetime import timedelta
from pathlib import Path

from corsheaders.defaults import default_headers
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-me')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    'accounts',
    'rbac',
    'audit',
    'system',
    'products',
    'orders',
    'customers.apps.CustomersConfig',
    'feedback',
    'announcement',
    'points',
    'points_mall.apps.PointsMallConfig',
    'seller_points.apps.SellerPointsConfig',
    'reviews',
    'reports',
    'promotion',
    'cart',
    'addresses',
    'chat.apps.ChatConfig',
    'complaints.apps.ComplaintsConfig',
    'tenants',
    'notification.apps.NotificationConfig',
    'logistics.apps.LogisticsConfig',
    'subsidy.apps.SubsidyConfig',
    'membership.apps.MembershipConfig',
    'tag_system.apps.TagSystemConfig',
    'shop_closure.apps.ShopClosureConfig',
    'shop_rating.apps.ShopRatingConfig',
    'approval.apps.ApprovalConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'common.middleware.TenantMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audit.middleware.OperationLogMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

REDIS_URL = os.getenv('REDIS_URL', '').strip()
if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [REDIS_URL]},
        },
    }
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
    _django_cache_dir = BASE_DIR / 'runtime' / 'django_cache'
    _django_cache_dir.mkdir(parents=True, exist_ok=True)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': str(_django_cache_dir),
        },
    }

DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite')

if DB_ENGINE == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'admin_db'),
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        },
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        },
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_UPLOAD_IMAGE_SIZE = 2 * 1024 * 1024

# 预留 OSS 配置，后续可切换云端存储
USE_OSS_STORAGE = os.getenv('USE_OSS_STORAGE', 'False').lower() == 'true'
ALIYUN_OSS_ACCESS_KEY_ID = os.getenv('ALIYUN_OSS_ACCESS_KEY_ID', '')
ALIYUN_OSS_ACCESS_KEY_SECRET = os.getenv('ALIYUN_OSS_ACCESS_KEY_SECRET', '')
ALIYUN_OSS_BUCKET_NAME = os.getenv('ALIYUN_OSS_BUCKET_NAME', '')
ALIYUN_OSS_ENDPOINT = os.getenv('ALIYUN_OSS_ENDPOINT', '')

# 短信 SDK（CredentialClient 亦会读同名环境变量）
ALIBABA_CLOUD_ACCESS_KEY_ID = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID', '')
ALIBABA_CLOUD_ACCESS_KEY_SECRET = os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET', '')

ALIYUN_SMS_ENABLED = os.getenv('ALIYUN_SMS_ENABLED', 'False').lower() == 'true'
# 注册验证码（API/API-Python 示例）
ALIYUN_SMS_SIGN_NAME = os.getenv('ALIYUN_SMS_SIGN_NAME', '速通互联验证码')
ALIYUN_SMS_TEMPLATE_CODE = os.getenv('ALIYUN_SMS_TEMPLATE_CODE', '100001')
# 找回密码验证码（API/ChangepwdAPITemp-Python 示例，可与注册不同签名/模板）
ALIYUN_SMS_RESET_SIGN_NAME = os.getenv('ALIYUN_SMS_RESET_SIGN_NAME', ALIYUN_SMS_SIGN_NAME)
ALIYUN_SMS_RESET_TEMPLATE_CODE = os.getenv('ALIYUN_SMS_RESET_TEMPLATE_CODE', '100003')
SMS_RESEND_SECONDS = int(os.getenv('SMS_RESEND_SECONDS', '10' if DEBUG else '60'))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'customers.authentication.CustomerJWTAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'common.pagination.StandardPagination',
    'EXCEPTION_HANDLER': 'common.exceptions.custom_exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# 商城 C 端：长期有效 + 滑动续期（与后台 30min 策略分离）
CUSTOMER_JWT_ACCESS_LIFETIME = timedelta(days=int(os.getenv('CUSTOMER_JWT_ACCESS_DAYS', '7')))
CUSTOMER_JWT_REFRESH_LIFETIME = timedelta(days=int(os.getenv('CUSTOMER_JWT_REFRESH_DAYS', '90')))

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:5173,http://localhost:5174',
    ).split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (*default_headers, 'x-tenant-code')

# 经 Nginx HTTPS 反代时识别协议与 Host
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

_csrf_trusted = os.getenv('CSRF_TRUSTED_ORIGINS', '').strip()
if _csrf_trusted:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_trusted.split(',') if o.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        o for o in CORS_ALLOWED_ORIGINS if o.startswith('https://')
    ]

ACTIVATION_LINK_BASE = os.getenv('ACTIVATION_LINK_BASE', 'http://localhost:5173')

EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '15'))
DEFAULT_FROM_EMAIL = os.getenv(
    'DEFAULT_FROM_EMAIL',
    EMAIL_HOST_USER or 'noreply@admin.local',
)

if EMAIL_HOST:
    EMAIL_BACKEND = os.getenv(
        'EMAIL_BACKEND',
        'django.core.mail.backends.smtp.EmailBackend',
    )
else:
    EMAIL_BACKEND = os.getenv(
        'EMAIL_BACKEND',
        'django.core.mail.backends.console.EmailBackend',
    )

LOGISTICS_PROVIDER = os.getenv('LOGISTICS_PROVIDER', 'mock').lower()
MOCK_LOGISTICS_STEP_HOURS = float(os.getenv('MOCK_LOGISTICS_STEP_HOURS', '6'))
KUAIDI100_CUSTOMER = os.getenv('KUAIDI100_CUSTOMER', '')
KUAIDI100_KEY = os.getenv('KUAIDI100_KEY', '')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
