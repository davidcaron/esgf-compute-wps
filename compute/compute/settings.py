"""
Django settings for compute project.

Generated by 'django-admin startproject' using Django 1.10.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import ConfigParser
import datetime
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

    def get_value(self, section, key, default, value_type=str, conv=None):
        try:
            if value_type == int:
                value = self.getint(section, key)
            elif value_type == float:
                value = self.getfloat(section, key)
            elif value_type == bool:
                value = self.getboolean(section, key)
            else:
                value = self.get(section, key)

                for replacement in self.defaults.iteritems():
                    if replacement[0] in value:
                        value = value.replace(*replacement)
        except ConfigParser.NoOptionError, ConfigParser.NoSectionError:
            value = default

            pass

        if conv is not None:
            value = conv(value)

        logger.info('Loaded "{}" for key "{}"'.format(value, key))

        return value

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '+a#&@l4!^)i5cn=!*ye^!42xcmyqs3l&j368ow^-y=3fs-txq6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = 'WPS_DEBUG' in os.environ
TEST = 'WPS_TEST' in os.environ

WPS_HOST = os.environ.get('WPS_HOST', '0.0.0.0')

ALLOWED_HOSTS = [ WPS_HOST ]

DJANGO_CONFIG_PATH = os.environ.get('DJANGO_CONFIG_PATH', '/etc/config/django.properties')

config = DjangoConfigParser.from_file(DJANGO_CONFIG_PATH, {
    '{host}': WPS_HOST,
})

add_allowed_hosts = config.get_value('default', 'allowed.hosts', '')

ALLOWED_HOSTS.extend(add_allowed_hosts.split(','))

#SESSION_COOKIE_NAME = 'wps_sessionid'
SESSION_COOKIE_NAME = config.get_value('default', 'session.cookie.name', 'wps_sessionid')

# Application definition
WPS_ENDPOINT = config.get_value('wps', 'wps.endpoint', 'https://{host}/wps')
WPS_STATUS_LOCATION = config.get_value('wps', 'wps.status_location', 'https://{host}/wps')
WPS_DAP = config.get_value('wps', 'wps.dap', 'true', bool)
WPS_DAP_URL = config.get_value('wps', 'wps.dap_url', 'https://{host}/threddsCWT/dodsC/public/{file_name}')
WPS_LOGIN_URL = config.get_value('wps', 'wps.login_url', 'https://{host}/wps/home/auth/login/openid')
WPS_PROFILE_URL = config.get_value('wps', 'wps.profile_url', 'https://{host}/wps/home/user/profile')
WPS_OAUTH2_CALLBACK = config.get_value('wps', 'wps.oauth2.callback', 'https://{host}/auth/callback')
WPS_OPENID_TRUST_ROOT = config.get_value('wps', 'wps.openid.trust.root', 'https://{host}/')
WPS_OPENID_RETURN_TO = config.get_value('wps', 'wps.openid.return.to', 'https://{host}auth/callback/openid')
WPS_OPENID_CALLBACK_SUCCESS = config.get_value('wps', 'wps.openid.callback.success', 'https://{host}/wps/home/auth/login/callback')
WPS_PASSWORD_RESET_URL = config.get_value('wps', 'wps.password.reset.url', 'https://{host}/wps/home/auth/reset')
WPS_CA_PATH = config.get_value('wps', 'wps.ca.path', '/tmp/certs')
WPS_LOCAL_OUTPUT_PATH = config.get_value('wps', 'wps.local.output.path', '/data/public')
WPS_USER_TEMP_PATH = config.get_value('wps', 'wps.local.output.path', '/tmp')
WPS_ADMIN_EMAIL = config.get_value('wps', 'wps.admin.email', 'admin@aims2.llnl.gov')

WPS_CACHE_PATH = config.get_value('cache', 'wps.cache.path', '/data/cache')
WPS_PARTITION_SIZE = config.get_value('cache', 'wps.partition.size', 10, int)
WPS_CACHE_CHECK = config.get_value('cache', 'wps.cache.check', 1, int, lambda x: datetime.timedelta(days=x))
WPS_GB_MAX_SIZE = config.get_value('cache', 'wps.gb.max.size', 2.097152e8, float)
WPS_CACHE_MAX_AGE = config.get_value('cache', 'wps.cache.max.age', 30, int, lambda x: datetime.timedelta(days=x))
WPS_CACHE_FREED_PERCENT = config.get_value('cache', 'wps.cache.freed.percent', 0.25, float)

WPS_EDAS_HOST = config.get_value('edas', 'wps.edas.host', 'aims2.llnl.gov')
WPS_EDAS_REQ_PORT = config.get_value('edas', 'wps.edas.req.port', 5670, int)
WPS_EDAS_RES_PORT = config.get_value('edas', 'wps.edas.res.port', 5671, int)
WPS_EDAS_TIMEOUT = config.get_value('edas', 'wps.edas.timeout', 30, int)

WPS_OPH_USER = config.get_value('ophidia', 'wps.oph.user', 'oph-test')
WPS_OPH_PASSWORD = config.get_value('ophidia', 'wps.oph.password', 'abcd')
WPS_OPH_HOST = config.get_value('ophidia', 'wps.oph.host', 'aims2.llnl.gov')
WPS_OPH_PORT = config.get_value('ophidia', 'wps.oph.port', 11732, int)
WPS_OPH_OUTPUT_PATH = config.get_value('ophidia', 'wps.oph.output.path', '/wps')
WPS_OPH_OUTPUT_URL = config.get_value('ophidia', 'wps.oph.output.url', 'https://aims2.llnl.gov/thredds/dodsC{output_path}/{output_name}.nc')
WPS_OPH_DEFAULT_CORES = config.get_value('ophidia', 'wps.oph.default.cores', 8, int)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': config.get_value('wps', 'wps.cache.path', '/tmp/django/cache'),
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

if TEST:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
else:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('POSTGRES_NAME', 'postgres'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
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
