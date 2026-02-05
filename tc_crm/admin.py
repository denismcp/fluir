from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Cliente, Contato, EtapaVenda, Oportunidade, Atividade, Proposta, ItemProposta, Etiqueta

@admin.register(EtapaVenda)
class EtapaVendaAdmin(admin.ModelAdmin):
    # O primeiro campo (nome) será o link para entrar no registro
    list_display = ('nome', 'ordem', 'permite_proposta', 'e_etapa_ganha')
    
    # Agora podemos tornar a ordem e as outras opções editáveis na lista
    list_editable = ('ordem', 'permite_proposta', 'e_etapa_ganha')
    
    ordering = ['ordem']

@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ('nome',)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'nome_fantasia', 'cnpj_cpf', 'cidade', 'estado')
    search_fields = ('razao_social', 'nome_fantasia', 'cnpj_cpf')
    list_filter = ('estado', 'regime_tributario')

@admin.register(Oportunidade)
class OportunidadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cliente', 'etapa', 'valor_estimado', 'data_fechamento_prevista')
    list_filter = ('etapa', 'tipo_oportunidade', 'status_operacional')
    search_fields = ('nome', 'cliente__razao_social')

# Registros simples para os demais modelos
admin.site.register(Contato)
admin.site.register(Atividade)
admin.site.register(Proposta)
admin.site.register(ItemProposta)