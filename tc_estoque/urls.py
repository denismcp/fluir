from django.urls import path
from . import views

app_name = 'estoque'

urlpatterns = [
    # Listagem e CRUD do Saldo de Estoque
   # path('saldos/', views.ItemEstoqueListView.as_view(), name='itemestoque_list'),
   # path('item/novo/', views.ItemEstoqueCreateView.as_view(), name='itemestoque_create'),
   # path('item/<int:pk>/', views.ItemEstoqueDetailView.as_view(), name='itemestoque_detail'),
   # path('item/<int:pk>/editar/', views.ItemEstoqueUpdateView.as_view(), name='itemestoque_update'),
    
    # Movimentações
   # path('movimentacoes/', views.MovimentacaoEstoqueListView.as_view(), name='movimentacao_list'),
    # Rota para criar uma nova movimentação vinculada a um ItemEstoque existente
   # path('saldos/<int:item_pk>/movimentar/', views.MovimentacaoEstoqueCreateView.as_view(), name='movimentacao_create'),
]