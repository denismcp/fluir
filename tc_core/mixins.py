# tc_core/mixins.py

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages

class PermissionRequiredMixin(AccessMixin):
    """
    Mixin de Django que checa se o usuário logado possui a permissão especificada
    (ou pertence a uma Regra que possui tal permissão), usando o modelo Usuario
    e Regra do tc_core.
    """
    permission_required = None
    # Rota de Login atualizada para o novo namespace
    login_url = reverse_lazy('tc_core:login') 
    raise_exception = False 

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Usuário não autenticado é enviado para o login
            return self.handle_no_permission()

        if self.permission_required:
            # A verificação é feita via request.user.has_perm()
            if not request.user.has_perm(self.permission_required):
                
                # Adiciona mensagem de erro para o usuário
                messages.error(
                    request, 
                    f"Acesso Negado: Você não tem permissão ('{self.permission_required}') para acessar esta página."
                )
                # Redireciona para o dashboard do core
                return redirect(reverse_lazy('tc_core:dashboard')) 
                
        return super().dispatch(request, *args, **kwargs)

    def get_permission_denied_message(self):
        return f"Você não tem permissão ('{self.permission_required}') para acessar esta página."