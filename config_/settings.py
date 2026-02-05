# tcmais_project/settings.py

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-m_k-!0(y8p)n5n8d7m!r$z=d0p9p+s7qg771h23^z6n4k2_r' # Substitua isto em produção

DEBUG = True

ALLOWED_HOSTS = ['*'] # Ajustar para produção

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
    
    # Apps de Terceiros
    'simple_history', # Histórico (Auditoria)
    'mptt',           # Para estruturas de categoria (se necessário)
    'django_filters', # Para filtros avançados (opcional, mas útil)

    # Nossas Apps Modulares do ERP
    'core',
    'crm',
    'produtos',
    'servicos',
    'estoque',
    'compras',
    'financeiro',
    'operacoes',
    'marketing',
    'relatorios',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Middleware para o histórico de modelos
    'simple_history.middleware.HistoryRequestMiddleware', 
]

ROOT_URLCONF = 'tcmais_project.urls'

# ############################################################################
# 2. CONFIGURAÇÕES DE TEMPLATES (Acesso aos Partials)
# ############################################################################

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # Adiciona o diretório raiz de templates
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

WSGI_APPLICATION = 'tcmais_project.wsgi.application'

# ############################################################################
# 3. CONFIGURAÇÕES DE AUTENTICAÇÃO
# ############################################################################

AUTH_USER_MODEL = 'core.Usuario' # Aponta para o nosso modelo customizado

LOGIN_URL = '/login/' # Rota de login (definida no core/urls.py)
LOGIN_REDIRECT_URL = '/' # Redireciona para o dashboard após login
LOGOUT_REDIRECT_URL = '/login/' # Redireciona para o login após logout

# ############################################################################
# 4. STATIC FILES (CSS, JS, Imagens)
# ############################################################################

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'), # Diretório raiz para arquivos estáticos
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # Para produção (collectstatic)

# ############################################################################
# 5. BANCO DE DADOS (SQLite para Desenvolvimento)
# ############################################################################

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ... (Restante das configurações Time Zone, Password Validators, etc.) ...