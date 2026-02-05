from django.urls import path
from . import views

app_name = 'relatorios'

urlpatterns = [
    # Dashboard de Indicadores e KPIs
    #path('', views.RelatorioDashboardView.as_view(), name='dashboard'),
    
    # ---------------------------
    # RELATÓRIOS FINANCEIROS
    # ---------------------------
    # Rastreia CR (Faturas) e CP (Despesas) vencidas e a vencer
    #path('vencimentos/', views.VencimentoFinanceiroView.as_view(), name='vencimento_financeiro'),
    
    # ---------------------------
    # RELATÓRIOS DE COMPRAS / AUDITORIA
    # ---------------------------
    # Compara Preço Estimado da Requisição vs. Preço Real do PO
    #path('auditoria-compras/', views.AuditoriaComprasView.as_view(), name='auditoria_compras'),
    #path('performance-fornecedores/', views.PerformanceFornecedoresView.as_view(), name='performance_fornecedores'),
    
    # ---------------------------
    # RELATÓRIOS DE MARKETING / VENDAS
    # ---------------------------
    # Calcula CAC e LTV (Life Time Value)
    #path('cac-ltv/', views.CAC_LTV_View.as_view(), name='cac_ltv'),
    
    # ---------------------------
    # RELATÓRIOS OPERACIONAIS
    # ---------------------------
    # Desempenho do Suporte (Tempo médio de resposta, Chamados por Cliente)
    #path('desempenho-suporte/', views.DesempenhoSuporteView.as_view(), name='desempenho_suporte'),
]