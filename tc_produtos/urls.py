from django.urls import path
from . import views

app_name = 'produtos'

urlpatterns = [
    # ########################################################################
    # PRODUTOS
    # ########################################################################
    path('produtos/', views.ProdutoListView.as_view(), name='produto_list'),
    path('produtos/novo/', views.ProdutoCreateView.as_view(), name='produto_create'),
    path('produtos/<int:pk>/', views.ProdutoDetailView.as_view(), name='produto_detail'),
    path('produtos/<int:pk>/editar/', views.ProdutoUpdateView.as_view(), name='produto_update'),
    path('produtos/<int:pk>/excluir/', views.ProdutoDeleteView.as_view(), name='produto_delete'),

    # ########################################################################
    # KITS DE MATERIAIS (Novas Rotas)
    # ########################################################################
    path('kits/', views.KitMaterialListView.as_view(), name='kit_list'),
    path('kits/novo/', views.KitMaterialCreateView.as_view(), name='kit_create'),
    path('kits/<int:pk>/editar/', views.KitMaterialUpdateView.as_view(), name='kit_update'),

    # ########################################################################
    # FORNECEDORES
    # ########################################################################
    path('fornecedores/', views.FornecedorListView.as_view(), name='fornecedor_list'),
    path('fornecedores/novo/', views.FornecedorCreateView.as_view(), name='fornecedor_create'),
    path('fornecedores/<int:pk>/', views.FornecedorDetailView.as_view(), name='fornecedor_detail'),
    path('fornecedores/<int:pk>/editar/', views.FornecedorUpdateView.as_view(), name='fornecedor_update'),
    path('fornecedores/<int:pk>/excluir/', views.FornecedorDeleteView.as_view(), name='fornecedor_delete'),
    # CONTATOS
    path('fornecedor/<int:pk>/contato/novo/', views.fornecedor_contato_add, name='fornecedor_contato_add'),
    path('contato/<int:pk>/editar/', views.fornecedor_contato_edit, name='fornecedor_contato_edit'),
    path('contato/<int:pk>/excluir/', views.fornecedor_contato_delete, name='fornecedor_contato_delete'),

    # ########################################################################
    # CATEGORIAS
    # ########################################################################
    path('categorias/', views.CategoriaProdutoListView.as_view(), name='categoria_list'),
    path('categorias/novo/', views.CategoriaProdutoCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaProdutoUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/excluir/', views.CategoriaProdutoDeleteView.as_view(), name='categoria_delete'),


    # ########################################################################
    # SERVIÇOS (Independente)
    # ########################################################################
    path('servicos/', views.ServicoListView.as_view(), name='servico_list'),
    path('servicos/novo/', views.ServicoCreateView.as_view(), name='servico_create'),
    path('servicos/<int:pk>/', views.ServicoDetailView.as_view(), name='servico_detail'),
    path('servicos/<int:pk>/editar/', views.ServicoUpdateView.as_view(), name='servico_update'),
    path('servicos/<int:pk>/excluir/', views.ProdutoDeleteView.as_view(), name='servico_delete'), # Reaproveita a lógica de exclusão
    
    # ########################################################################
    # PLANILHAS E IMPORTAÇÕES
    # ########################################################################
    path('produtos/planilha/', views.ProdutoSheetView.as_view(), name='produto_sheet'),
    path('servicos/planilha/', views.ServicoSheetView.as_view(), name='servico_sheet'),
    path('produtos/importar/', views.ProdutoImportView.as_view(), name='produto_import'),
    path('servicos/importar/', views.ServicoImportView.as_view(), name='servico_import'),
    path('item/update-cell/', views.update_produto_cell, name='update_cell'),
    # Rota geral que o utils pode usar se necessário
    path('baixar-template/', views.baixar_template_importacao, name='baixar_template'),
    # Rota para importação de documentos para fornecedores
    path('fornecedor/<int:pk>/documento/novo/', views.fornecedor_documento_add, name='fornecedor_documento_add'),
    path('documento/<int:pk>/excluir/', views.fornecedor_documento_delete, name='fornecedor_documento_delete'),
]