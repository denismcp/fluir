from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Rotas do Admin Django
    path('admin/', admin.site.urls),
    
    # 1. Rotas do CORE (Dashboard e Auth - A url raiz '')
    # O include do core deve ser o primeiro para capturar a rota raiz e de login/logout
    path('', include('core.urls')), 
    
    # 2. Rotas Modulares do ERP
    path('crm/', include('crm.urls', namespace='crm')),
    path('produtos/', include('produtos.urls', namespace='produtos')),
    path('servicos/', include('servicos.urls', namespace='servicos')),
    path('estoque/', include('estoque.urls', namespace='estoque')),
    path('compras/', include('compras.urls', namespace='compras')),
    path('financeiro/', include('financeiro.urls', namespace='financeiro')),
    path('operacoes/', include('operacoes.urls', namespace='operacoes')),
    path('marketing/', include('marketing.urls', namespace='marketing')),
    path('relatorios/', include('relatorios.urls', namespace='relatorios')), # Novo App
    
]

# Configuração para servir arquivos estáticos e de mídia em ambiente de desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)