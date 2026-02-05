from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # Rotas de Clientes
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    path('clientes/novo/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/', views.ClienteDetailView.as_view(), name='cliente_detail'),
    path('clientes/<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:pk>/excluir/', views.ClienteDeleteView.as_view(), name='cliente_delete'),

    # Rotas de Contatos
    path('contatos/novo/<int:cliente_pk>/', views.ContatoCreateView.as_view(), name='contato_create'),
    path('contatos/<int:pk>/editar/', views.ContatoUpdateView.as_view(), name='contato_update'),
    path('contatos/<int:pk>/excluir/', views.ContatoDeleteView.as_view(), name='contato_delete'),
    
    # Rotas de Kanban e Oportunidades
    path('kanban/', views.KanbanView.as_view(), name='kanban'),
    path('oportunidades/novo/', views.OportunidadeCreateView.as_view(), name='oportunidade_create'),
    path('oportunidades/atualizar-etapa/', views.atualizar_etapa_oportunidade, name='atualizar_etapa'),
    path('oportunidades/<int:pk>/', views.OportunidadeDetailView.as_view(), name='oportunidade_detail'),
    path('oportunidades/<int:oportunidade_pk>/atividade/novo/', views.AtividadeCreateView.as_view(), name='atividade_create'),
    path('atividades/<int:pk>/editar/', views.AtividadeUpdateView.as_view(), name='atividade_update'),
    path('oportunidade/<int:pk>/editar/', views.OportunidadeUpdateView.as_view(), name='oportunidade_update'),
    path('oportunidade/<int:pk>/fechamento/', views.oportunidade_fechamento_view, name='oportunidade_fechamento'),
    path('oportunidade/<int:pk>/concluir/', views.oportunidade_concluir, name='oportunidade_concluir'),
    path('oportunidades/', views.OportunidadeListView.as_view(), name='oportunidade_list'),
    path('oportunidade/<int:pk>/duplicar/', views.oportunidade_duplicar, name='oportunidade_duplicar'),

    #Rotas de Propostas
    path('oportunidades/<int:oportunidade_pk>/proposta/novo/', views.PropostaCreateView.as_view(), name='proposta_create'),
    path('proposta/<int:pk>/itens/', views.PropostaItensView.as_view(), name='proposta_itens'),
    path('proposta/<int:pk>/item/add/', views.item_proposta_add, name='item_proposta_add'),
    path('proposta/<int:pk>/total-fragment/', views.proposta_total_fragment, name='proposta_total_fragment'),
    path('proposta/item/<int:pk>/atualizar/', views.atualizar_item_proposta, name='item_proposta_atualizar'),
    path('proposta/item/<int:pk>/excluir/', views.excluir_item_proposta, name='item_proposta_excluir'),
    path('proposta/<int:pk>/editar/', views.PropostaUpdateView.as_view(), name='proposta_update'),
    path('propostas/', views.PropostaListView.as_view(), name='proposta_list'),
    path('proposta/<int:pk>/duplicar/', views.proposta_duplicar, name='proposta_duplicar'),
    path('proposta/<int:pk>/excluir/', views.PropostaDeleteView.as_view(), name='proposta_delete'),

    # ROTA PARA O PDF DE COMPARAÇÃO
    path('oportunidade/<int:oport_id>/comparativo-pdf/', views.proposta_comparativo_pdf_view, name='proposta_comparativo_pdf'),
    path('oportunidade/<int:oport_id>/pdf/', views.proposta_comparativo_pdf_view, name='proposta_comparativo_pdf'),
    path('oportunidade/<int:oport_id>/pdf/completa/', views.proposta_pdf_view, {'tipo': 'completa'}, name='proposta_pdf_completa'),
    path('oportunidade/<int:oport_id>/pdf/resumo/', views.proposta_pdf_view, {'tipo': 'resumo'}, name='proposta_pdf_resumo'),

    # Rotas de Fornecedores
    path('fornecedor/modal/novo/', views.fornecedor_modal_create, name='fornecedor_modal_create'),

    #Rota Dashboard CRM
    path('performance/', views.dashboard_vendas_view, name='dashboard_vendas'),
]