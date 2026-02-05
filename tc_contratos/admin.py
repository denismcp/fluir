from django.contrib import admin
from .models import Contrato
from simple_history.admin import SimpleHistoryAdmin

@admin.register(Contrato)
class ContratoAdmin(SimpleHistoryAdmin):
    # Listamos apenas os campos que temos certeza que existem no models.py atual
    list_display = ('numero_contrato', 'tipo_contrato', 'valor_mensal')
    # Removido list_filter e search_fields temporariamente para evitar erros de campos inexistentes