from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Usuario
from tc_crm.models import MetaMensal

@receiver(post_save, sender=Usuario)
def sincronizar_meta_mensal(sender, instance, **kwargs):
    # Verifica se o usuário tem uma meta prevista definida no cadastro
    if instance.departamento == 'comercial' and instance.meta_mensal_prevista:
        hoje = timezone.now()
        
        # Busca ou cria a meta para o vendedor no mês/ano atual
        MetaMensal.objects.update_or_create(
            vendedor=instance,
            mes=hoje.month,
            ano=hoje.year,
            defaults={'valor_objetivo': instance.meta_mensal_prevista}
        )