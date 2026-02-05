from django.urls import path
from . import views

# O namespace oficial que deve ser usado no Sidebar e templates
app_name = 'contratos'

urlpatterns = [
    # Rotas Principais
    path('', views.ContratoListView.as_view(), name='contrato_list'),
    path('<int:pk>/', views.ContratoDetailView.as_view(), name='contrato_detail'),
    path('novo/', views.ContratoCreateView.as_view(), name='contrato_create'),
    path('<int:pk>/editar/', views.ContratoUpdateView.as_view(), name='contrato_update'),
    
    # Endpoints AJAX (Unificados e sem duplicidade)
    path('ajax/carregar-oportunidades/', views.carregar_oportunidades_disponiveis, name='carregar_oportunidades'),
    path('ajax/obter-valor-proposta/', views.obter_valor_proposta, name='obter_valor_proposta'),
    path('ajax/calcular-renovacao/', views.calcular_renovacao, name='calcular_renovacao'),
]