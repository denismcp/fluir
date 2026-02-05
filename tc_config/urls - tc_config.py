from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Rotas do Admin Django
    path('admin/', admin.site.urls),
    
    # 1. Rotas do CORE (Dashboard e Auth - A url raiz '')
    path('', include('tc_core.urls', namespace='tc_core')),    
    
    # 2. Rotas Modulares do ERP (Prefixadas)
    path('crm/', include('tc_crm.urls', namespace='crm')),
    path('produtos/', include('tc_produtos.urls', namespace='produtos')),
    path('servicos/', include('tc_servicos.urls', namespace='servicos')),
    path('estoque/', include('tc_estoque.urls', namespace='estoque')),
    path('compras/', include('tc_compras.urls', namespace='compras')),
    path('financeiro/', include('tc_financeiro.urls', namespace='financeiro')),
    path('contratos/', include('tc_contratos.urls', namespace="contratos")), 
    path('operacoes/', include('tc_operacoes.urls', namespace='operacoes')),
    path('marketing/', include('tc_marketing.urls', namespace='marketing')),
    path('relatorios/', include('tc_relatorios.urls', namespace='relatorios')), 
    # Fluxo de Recuperação de Senha
    path('reset_password/', auth_views.PasswordResetView.as_view(
        template_name="registration/password_reset.html"), name="reset_password"),
        
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(
        template_name="registration/password_reset_sent.html"), name="password_reset_done"),
        
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name="registration/password_reset_form.html"), name="password_reset_confirm"),
        
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name="registration/password_reset_done.html"), name="password_reset_complete"),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)