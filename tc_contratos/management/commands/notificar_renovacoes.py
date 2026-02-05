# tc_contratos/management/commands/notificar_renovacoes.py

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from tc_contratos.models import Contrato

class Command(BaseCommand):
    help = 'Envia e-mail para contratos que vencem nos próximos 30 dias'

    def handle(self, *args, **kwargs):
        hoje = timezone.now().date()
        prazo = hoje + timedelta(days=30)
        
        # Filtra contratos ativos que vencem nos próximos 30 dias
        contratos = Contrato.objects.filter(
            situacao='ATIVO',
            data_proxima_renovacao__range=[hoje, prazo]
        )

        if not contratos:
            self.stdout.write("Nenhum contrato vencendo em breve.")
            return

        for contrato in contratos:
            cliente_fornecedor = contrato.cliente.razao_social if contrato.cliente else contrato.fornecedor.razao_social
            
            assunto = f"ALERTA: Renovação de Contrato - {contrato.numero_contrato}"
            mensagem = (
                f"Olá,\n\n"
                f"O contrato {contrato.numero_contrato} com {cliente_fornecedor} "
                f"está próximo do vencimento/renovação.\n\n"
                f"Data da Renovação: {contrato.data_proxima_renovacao.strftime('%d/%m/%Y')}\n"
                f"Valor Atual: R$ {contrato.valor_mensal}\n\n"
                f"Por favor, verifique a necessidade de reajuste ou termo aditivo."
            )
            
            # Envia para os administradores ou e-mail específico
            send_mail(
                assunto,
                mensagem,
                None,  # Usa o DEFAULT_FROM_EMAIL
                ['comercial@suaempresa.com.br'], # E-mails de destino
                fail_silently=False,
            )
            
            self.stdout.write(self.style.SUCCESS(f'Notificação enviada para {contrato.numero_contrato}'))