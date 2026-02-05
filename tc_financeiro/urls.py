from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    # Dashboard Principal
    path('dashboard/', views.FinancialDashboardView.as_view(), name='dashboard'),

    # --- GESTÃO DE RECEITAS (FATURAS / CONTAS A RECEBER) ---
    path('faturas/', views.FaturaListView.as_view(), name='fatura_list'),
    path('faturas/nova/', views.FaturaCreateView.as_view(), name='fatura_create'),
    path('faturas/planilha/', views.FaturaPlanilhaView.as_view(), name='fatura_planilha'),
    path('faturas/editar/<int:pk>/', views.FaturaUpdateView.as_view(), name='fatura_update'),
    path('faturas/detalhe/<int:pk>/', views.FaturaDetailView.as_view(), name='fatura_detail'),
    
    # ROTA NOVA (ESSENCIAL PARA O SIDEBAR FUNCIONAR):
    path('faturas/confirmar-liquidacao/<int:pk>/', views.fatura_confirm_liquidar, name='fatura_confirm_liquidar'),
    
    path('faturas/<int:pk>/receber-agora/', views.fatura_receber_agora, name='fatura_receber_agora'),
    path('faturas/excluir/<int:pk>/', views.fatura_delete, name='fatura_delete'),

    # --- RECIBOS E DOCUMENTOS PDF
    path('faturas/recibo/<int:pk>/', views.fatura_recibo, name='fatura_recibo'),

    # --- GESTÃO DE DESPESAS (CONTAS A PAGAR) ---
    path('despesas/', views.DespesaListView.as_view(), name='despesa_list'),
    path('despesas/nova/', views.DespesaCreateView.as_view(), name='despesa_create'),
    path('despesas/planilha/', views.DespesaPlanilhaView.as_view(), name='despesa_planilha'),
    path('despesas/editar/<int:pk>/', views.DespesaUpdateView.as_view(), name='despesa_update'),
    path('despesas/detalhe/<int:pk>/', views.DespesaDetailView.as_view(), name='despesa_detail'),
    path('despesas/excluir/<int:pk>/', views.despesa_delete, name='despesa_delete'),

    # --- GESTÃO DE CONTRATOS ---
    path('contratos/', views.ContratoListView.as_view(), name='contrato_list'),
    path('contratos/novo/', views.ContratoCreateView.as_view(), name='contrato_create'),

    # --- FERRAMENTAS E SERVIÇOS ---
    path('importar-xml/', views.importar_xml, name='importar_xml'),
    path('metas/', views.MetaVendaListView.as_view(), name='metavenda_list'),
]