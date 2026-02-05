from django.urls import path
from . import views

app_name = 'servicos'

urlpatterns = [
    # Rotas de Serviços (Servico)
    path('', views.ServicoListView.as_view(), name='servico_list'),
    path('novo/', views.ServicoCreateView.as_view(), name='servico_create'),
    path('<int:pk>/', views.ServicoDetailView.as_view(), name='servico_detail'),
    path('<int:pk>/editar/', views.ServicoUpdateView.as_view(), name='servico_update'),
    path('<int:pk>/excluir/', views.ServicoDeleteView.as_view(), name='servico_delete'),
    
    # Rotas de Categorias (CategoriaServico)
    path('categorias/', views.CategoriaServicoListView.as_view(), name='categoria_list'),
]