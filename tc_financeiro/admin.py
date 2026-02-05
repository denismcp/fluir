from django.contrib import admin
from .models import Fatura, Despesa, MetaVenda
from simple_history.admin import SimpleHistoryAdmin

@admin.register(Fatura)
class FaturaAdmin(SimpleHistoryAdmin):
    # Exibição na listagem com foco em Saldos e Status
    list_display = ('numero_documento', 'cliente', 'data_vencimento', 'valor_total', 'valor_saldo', 'status')
    list_filter = ('status', 'data_vencimento', 'forma_pagamento', 'tipo_titulo')
    search_fields = ('numero_documento', 'cliente__razao_social', 'cliente__nome_fantasia')
    
    # Campos que o sistema calcula sozinho não devem ser editáveis
    readonly_fields = ('uuid', 'valor_total', 'valor_saldo', 'criado_em', 'alterado_em')

    fieldsets = (
        ('Identificação e Origem', {
            'fields': ('uuid', 'cliente', 'contrato', 'numero_documento', 'descricao', 'tipo_titulo', 'origem')
        }),
        ('Controle Financeiro', {
            'fields': (('valor_original', 'valor_desconto'), ('valor_juros', 'valor_multa', 'valor_acrescimo'), ('valor_total', 'valor_pago', 'valor_saldo'))
        }),
        ('Datas e Competência', {
            'fields': (('data_emissao', 'data_vencimento'), ('data_liquidacao', 'data_competencia'))
        }),
        ('Dados de Pagamento (Boleto/Pix)', {
            'fields': ('forma_pagamento', 'banco_nome', 'chave_pix', 'linha_digitavel', 'codigo_barras')
        }),
        ('Fiscal e Cobrança', {
            'fields': (('numero_nf', 'serie_nf'), 'chave_acesso_nf', ('nivel_cobranca', 'ultima_cobranca'))
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
    )

@admin.register(Despesa)
class DespesaAdmin(SimpleHistoryAdmin):
    # Removido 'pago' e 'centro_custo_id' para sanar os erros de sistema
    list_display = ('numero_documento', 'descricao', 'fornecedor', 'data_vencimento', 'valor_total', 'status')
    list_filter = ('status', 'data_vencimento', 'forma_pagamento', 'tipo_titulo')
    search_fields = ('numero_documento', 'descricao', 'fornecedor__razao_social')
    
    readonly_fields = ('uuid', 'valor_total', 'valor_saldo', 'criado_em', 'alterado_em')

    fieldsets = (
        ('Identificação', {
            'fields': ('uuid', 'fornecedor', 'numero_documento', 'descricao', 'tipo_titulo')
        }),
        ('Financeiro', {
            'fields': (('valor_original', 'valor_desconto'), ('valor_juros', 'valor_multa'), ('valor_total', 'valor_pago', 'valor_saldo'))
        }),
        ('Datas', {
            'fields': (('data_emissao', 'data_vencimento'), ('data_liquidacao', 'data_competencia'))
        }),
        ('Pagamento', {
            'fields': ('forma_pagamento', 'status', 'comprovante')
        }),
    )

@admin.register(MetaVenda)
class MetaVendaAdmin(SimpleHistoryAdmin):
    list_display = ('usuario', 'ano')