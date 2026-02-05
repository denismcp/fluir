from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from simple_history.admin import SimpleHistoryAdmin
from .models import Usuario, Regra 

class UsuarioAdmin(BaseUserAdmin, SimpleHistoryAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'regra')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'regra', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'regra')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'regra__nome')

admin.site.register(Usuario, UsuarioAdmin)

@admin.register(Regra)
class RegraAdmin(SimpleHistoryAdmin):
    list_display = ('nome', 'descricao') # <-- Corrigiremos a descrição abaixo
    filter_horizontal = ('permissoes',) # <-- Este campo JÁ EXISTE no seu modelo Regra
    search_fields = ('nome',)