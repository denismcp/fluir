import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-m_k-!0(y8p)n5n8d7m!r$z=d0p9p+s7qg771h23^z6n4k2_r' 

DEBUG = False

ALLOWED_HOSTS = ['qa.tcdobrasil.com.br', '10.10.0.102', '10.10.0.101', 'localhost']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ############################################################################
# 1. APPS INSTALADAS
# ############################################################################

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_htmx',
    
    # Apps de Terceiros
    'simple_history',
    'mptt',          
    'crispy_forms',
    'crispy_bootstrap5',

    # Nossas Apps Modulares do ERP (Prefixadas)
    'tc_contratos',
    'tc_core',
    'tc_crm',
    'tc_produtos',
    'tc_servicos',
    'tc_estoque',
    'tc_compras',
    'tc_financeiro',
    'tc_operacoes',
    'tc_marketing',
    'tc_relatorios',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    'simple_history.middleware.HistoryRequestMiddleware', 
]

ROOT_URLCONF = 'tc_config.urls' 

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'tc_config.wsgi.application'
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ############################################################################
# 3. CONFIGURAÇÕES DE AUTENTICAÇÃO
# ############################################################################

AUTH_USER_MODEL = 'tc_core.Usuario' # <--- ATUALIZADO

LOGIN_URL = '/login/' 
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# ############################################################################
# 4. STATIC FILES (CSS, JS, Imagens)
# ############################################################################

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'), 
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') 

# ############################################################################
# 5. BANCO DE DADOS (SQLite para Desenvolvimento)
# ############################################################################

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
#}

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL')
    )
}

# Configurações de Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True

# ############################################################################
# 6. SERVIDOR SMTP
# ############################################################################


# 6. SERVIDOR SMTP (Configuração para envio de e-mails)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email@gmail.com'  # Substitua pelo seu e-mail
EMAIL_HOST_PASSWORD = 'sua-senha-de-aplicativo'  # Substitua pela senha de app gerada no Google

# E-mail que aparecerá como remetente
DEFAULT_FROM_EMAIL = 'TCMAIS ERP <seu-email@gmail.com>'

# URLs de Autenticação
LOGIN_URL = '/login/' 
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'