from django.urls import path
from . import views

app_name = 'operacoes'

urlpatterns = [
    # ---------------------------
    # CHAMADOS (ITSM)
    # ---------------------------
    path('chamados/', views.ChamadoListView.as_view(), name='chamado_list'),
    path('chamados/novo/', views.ChamadoCreateView.as_view(), name='chamado_create'),
    path('chamados/<int:pk>/', views.ChamadoDetailView.as_view(), name='chamado_detail'),
    path('chamados/<int:pk>/editar/', views.ChamadoUpdateView.as_view(), name='chamado_update'),
    
    # Interações/Respostas (Para ser usado via HTMX no Chamado Detail)
    path('chamados/<int:chamado_pk>/interagir/', views.InteracaoChamadoCreateView.as_view(), name='chamado_interagir'),
    path('chamados/<int:chamado_pk>/solucao/', views.SolucaoChamadoCreateView.as_view(), name='chamado_solucao'),
    
    # ---------------------------
    # ATIVOS (CMDB)
    # ---------------------------
    path('ativos/', views.AtivoListView.as_view(), name='ativo_list'),
    path('ativos/novo/', views.AtivoCreateView.as_view(), name='ativo_create'),
    path('ativos/<int:pk>/', views.AtivoDetailView.as_view(), name='ativo_detail'),
    path('ativos/<int:pk>/editar/', views.AtivoUpdateView.as_view(), name='ativo_update'),
    
    # ---------------------------
    # ORDENS DE SERVIÇO (OS)
    # ---------------------------
    path('ordens/', views.OrdemServicoListView.as_view(), name='ordemservico_list'),
    path('ordens/nova/', views.OrdemServicoCreateView.as_view(), name='ordemservico_create'),
    path('ordens/<int:pk>/', views.OrdemServicoDetailView.as_view(), name='ordemservico_detail'),
    
    # ---------------------------
    # CADASTROS MESTRES (Para a sidebar)
    # ---------------------------
    path('categorias/', views.CategoriaOperacaoListView.as_view(), name='categoria_list'),
    path('fabricantes/', views.FabricanteListView.as_view(), name='fabricante_list'),
]