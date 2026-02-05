from django.urls import path
from . import views

app_name = 'compras'

urlpatterns = [
    # ---------------------------
    # ROTAS DE REQUISIÇÃO DE COMPRA
    # ---------------------------
    #path('requisicoes/', views.RequisicaoCompraListView.as_view(), name='requisicao_list'),
    #path('requisicoes/nova/', views.RequisicaoCompraCreateView.as_view(), name='requisicao_create'),
    #path('requisicoes/<int:pk>/', views.RequisicaoCompraDetailView.as_view(), name='requisicao_detail'),
    #path('requisicoes/<int:pk>/editar/', views.RequisicaoCompraUpdateView.as_view(), name='requisicao_update'),
    #path('requisicoes/<int:pk>/aprovar/', views.AprovacaoRequisicaoCreateView.as_view(), name='requisicao_aprovar'),
    
    # Rotas de Item da Requisição (para uso no modal da DetailView)
    #path('requisicoes/<int:requisicao_pk>/item/novo/', views.ItemRequisicaoCreateView.as_view(), name='itemrequisicao_create'),
    
    # ---------------------------
    # ROTAS DE PEDIDO DE COMPRA (PO)
    # ---------------------------
    #path('pedidos/', views.PedidoCompraListView.as_view(), name='pedidocompra_list'),
    # Cria PO a partir de Requisição APENAS SE APROVADA
    #path('pedidos/nova/<int:requisicao_pk>/', views.PedidoCompraCreateView.as_view(), name='pedidocompra_create'), 
    #path('pedidos/<int:pk>/', views.PedidoCompraDetailView.as_view(), name='pedidocompra_detail'),
    
    # Rotas de Recebimento de Item (para uso no modal da PedidoCompraDetail)
    #path('pedidos/item/<int:item_pk>/receber/', views.RecebimentoItemCreateView.as_view(), name='recebimento_create'),
    
    # ---------------------------
    # ROTAS DE CADASTRO MESTRE (Para a sidebar)
    # ---------------------------
    #path('centros-custo/', views.CentroCustoListView.as_view(), name='centrocusto_list'),
]