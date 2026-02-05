from django.contrib import admin
from .models import Fornecedor, CategoriaProduto, Produto, PrecoFornecedor, KitMaterial, ItemKit, FornecedorContato

class FornecedorContatoInline(admin.TabularInline):
    model = FornecedorContato
    extra = 1

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'cnpj', 'tipo_fornecedor')
    search_fields = ('razao_social', 'cnpj', 'email')
    list_filter = ('tipo_fornecedor', 'e_distribuidor')
    # Permite selecionar múltiplas categorias de forma amigável
    filter_horizontal = ('categorias_fornecidas',) 
    # Adiciona a gestão de contatos diretamente dentro do fornecedor
    inlines = [FornecedorContatoInline]

@admin.register(CategoriaProduto)
class CategoriaProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}

class PrecoFornecedorInline(admin.TabularInline):
    model = PrecoFornecedor
    extra = 1

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('codigo_interno', 'nome', 'categoria', 'tipo_produto', 'preco_venda_padrao')
    list_filter = ('categoria', 'tipo_produto')
    search_fields = ('nome', 'codigo_interno')
    inlines = [PrecoFornecedorInline]

class ItemKitInline(admin.TabularInline):
    model = ItemKit
    extra = 1

@admin.register(KitMaterial)
class KitMaterialAdmin(admin.ModelAdmin):
    list_display = ('nome', 'custo_total_estimado')
    inlines = [ItemKitInline]