from django.urls import path
from . import views

app_name = 'marketing'

urlpatterns = [
    # ---------------------------
    # GASTOS DE MARKETING
    # ---------------------------
    path('gastos/', views.GastoMarketingListView.as_view(), name='gastomarketing_list'),
    path('gastos/novo/', views.GastoMarketingCreateView.as_view(), name='gastomarketing_create'),
    path('gastos/<int:pk>/editar/', views.GastoMarketingUpdateView.as_view(), name='gastomarketing_update'),
    
    # ---------------------------
    # CADASTROS MESTRES (Canais)
    # ---------------------------
    path('canais/', views.CanalMarketingListView.as_view(), name='canalmarketing_list'),
    path('canais/novo/', views.CanalMarketingCreateView.as_view(), name='canalmarketing_create'),
    # path('canais/<int:pk>/editar/', views.CanalMarketingUpdateView.as_view(), name='canalmarketing_update'),
]