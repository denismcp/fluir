from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# AJUSTE 1: Alterado para 'tc_core' para bater com a Sidebar e as Views
app_name = 'tc_core'

urlpatterns = [
    # Rotas de Autenticação
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'), 
    
    # Rota Principal (Dashboard)
    path('', views.DashboardView.as_view(), name='dashboard'),
        
    # Rotas Globais/Utilidade
    path('search/results/', views.search_results_view, name='search_results'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    
    # AJUSTE 2: Novas rotas para Gestão de Usuários e Vendedores
    # Elas agora apontam para as funções que adicionamos no seu views.py
    path('usuarios/', views.usuario_list_view, name='usuario_list'),
    path('usuarios/novo/', views.usuario_create_view, name='usuario_create'),
    path('usuarios/editar/<int:pk>/', views.usuario_update_view, name='usuario_update'),

    # Rota Regras e Papeis
    path('regras/', views.regra_list_view, name='regra_list'),
    path('regras/nova/', views.regra_create_view, name='regra_create'),
    path('regras/editar/<int:pk>/', views.regra_update_view, name='regra_update'),

    # Rota para botão ajuda
    path('ajuda/acessos/', views.ajuda_acessos_view, name='ajuda_acessos'),

    # Rota de Metas Globais
    path('metas/', views.meta_list_view, name='meta_list'),
    path('metas/nova/', views.meta_create_view, name='meta_create'),
    path('metas/editar/<int:pk>/', views.meta_update_view, name='meta_update'),
    path('metas/excluir/<int:pk>/', views.meta_delete_view, name='meta_delete'),
]