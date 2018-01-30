"""
Django settings for compute project.

Generated by 'django-admin startproject' using Django 1.10.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import ConfigParser
import logging
import os

logger = logging.getLogger('settings')

class DjangoConfigParser(ConfigParser.ConfigParser):
    def __init__(self, defaults):
        self.defaults = defaults

        ConfigParser.ConfigParser.__init__(self)

    @classmethod
    def from_file(cls, file_path, defaults):
        config = cls(defaults)

        config.read([file_path])

        return config

    def get_value(self, key, default, value_type=str):
        try:
            if value_type == int:
                value = self.getint('default', key)
            elif value_type == float:
                value = self.getfloat('default', key)
            elif value_type == bool:
                value = self.getboolean('default', key)
            else:
                value = self.get('default', key)

                for replacement in self.defaults.iteritems():
                    if replacement[0] in value:
                        value = value.replace(*replacement)
        except ConfigParser.NoOptionError:
            value = default_value

            pass

        logger.info('Loaded "{}" for key "{}"'.format(value, key))

        return value

SESSION_COOKIE_NAME = 'wps_sessionid'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+a#&@l4!^)i5cn=!*ye^!42xcmyqs3l&j368ow^-y=3fs-txq6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = 'WPS_DEBUG' in os.environ

HOST = os.environ.get('WPS_HOST', '0.0.0.0')

ALLOWED_HOSTS = [ HOST ]

config = DjangoConfigParser.from_file('/etc/config/django.properties', {
    '{host}': HOST,
})

# Application definition

WPS_ENDPOINT = config.get_value('wps.endpoint', 'https://{host}/wps')
WPS_STATUS_LOCATION = config.get_value('wps.status_location', 'https://{host}/wps')
WPS_DAP = config.get_value('wps.dap', 'true', bool)
WPS_DAP_URL = config.get_value('wps.dap_url', 'https://{host}/threddsCWT/dodsC/public/{file_name}')
WPS_LOGIN_URL = config.get_value('wps.login_url', 'https://{host}/wps/home/auth/login/openid')
WPS_PROFILE_URL = config.get_value('wps.profile_url', 'https://{host}/wps/home/user/profile')
WPS_OAUTH2_CALLBACK = config.get_value('wps.oauth2.callback', 'https://{host}/auth/callback')
WPS_OPENID_TRUST_ROOT = config.get_value('wps.openid.trust.root', 'https://{host}/')
WPS_OPENID_RETURN_TO = config.get_value('wps.openid.return.to', 'https://{host}auth/callback/openid')
WPS_OPENID_CALLBACK_SUCCESS = config.get_value('wps.openid.callback.success', 'https://{host}/wps/home/auth/login/callback')
WPS_PASSWORD_RESET_URL = config.get_value('wps.password.reset.url', 'https://{host}/wps/home/auth/reset')

WPS_CACHE_GB_MAX_SIZE = 1.073741824e11

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache'
    }
}

INSTALLED_APPS = [
    'wps',
    'webpack_loader',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

try:
    import django_nose
except:
    pass
else:
    INSTALLED_APPS.append('django_nose')

    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

    if DEBUG:
        NOSE_ARGS = [
            '--with-coverage',
            '--cover-package=wps.auth,wps.backends,wps.management,wps.models,wps.tasks,wps.views,wps.wps_xml',
        ]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'compute.urls'

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

WSGI_APPLICATION = 'compute.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {}

if DEBUG:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
else:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', '1234'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
    }

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'wps', 'webapp', 'src'),
        ]
    }
]

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'

if DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, 'assets')
else:
    STATIC_ROOT = '/var/www/static'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'assets'),
)

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'js/',
        'STATS_FILE': os.path.join(BASE_DIR, 'wps', 'webapp', 'webpack-stats.json'),
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s][%(asctime)s][%(filename)s[%(funcName)s:%(lineno)s]] %(message)s',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'cwt_rotating': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': './wps_cwt.txt',
            'maxBytes': 1024000,
            'backupCount': 2,
        },
    },
    'loggers': {
        'cwt': {
            'handlers': ['cwt_rotating'],
            'propagate': False,
            'level': 'DEBUG',
        },
        'wps': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG',
        }
    }
}
