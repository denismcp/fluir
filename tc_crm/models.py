from django.db import models
from django.conf import settings
from django.utils import timezone
from simple_history.models import HistoricalRecords
from django.db import models
from django.db.models import Sum, F, DecimalField
from django.utils.translation import gettext_lazy as _
from django.utils.http import urlencode
from decimal import Decimal
from django.apps import apps
import math

# Modelo de Etiqueta (Tag) para classificação de Clientes
class Etiqueta(models.Model):
    """
    Modelo para Etiquetas (ex: Setor, Porte, Origem) que podem ser associadas a Clientes.
    """
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Etiqueta") 

    class Meta:
        verbose_name = "Etiqueta"
        verbose_name_plural = "Etiquetas"
        ordering = ['nome']

    def __str__(self):
        return self.nome

# Modelo para os Clientes (Empresas)
class Cliente(models.Model):
    # Choices de Tributação
    class RegimeTributario(models.TextChoices):
        SIMPLES = 'simples', _('Simples Nacional')
        PRESUMIDO = 'presumido', _('Lucro Presumido')
        REAL = 'real', _('Lucro Real')
        
    class TipoContribuinte(models.TextChoices):
        CONTRIBUINTE = 'contribuinte', _('Contribuinte ICMS')
        NAO = 'nao_contribuinte', _('Não Contribuinte')
        ISENTO = 'isento', _('Contribuinte Isento (IE)')

    # --- 1. CABEÇALHO ---
    razao_social = models.CharField(max_length=255, verbose_name="Razão Social")
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nome Fantasia")
    cnpj_cpf = models.CharField(max_length=18, unique=True, blank=True, null=True, verbose_name="CNPJ / CPF")
    
    # --- 2. ENDEREÇO & CONTATO EMPRESARIAL (Sincronizado com API Receita) ---
    cep = models.CharField(max_length=9, blank=True, null=True, verbose_name="CEP")
    endereco = models.CharField(max_length=255, blank=True, null=True, verbose_name="Logradouro")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    estado = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado (UF)")
    
    # Novos campos validados para os dados mestres da empresa
    email_corporativo = models.EmailField(max_length=255, blank=True, null=True, verbose_name="E-mail Principal (Empresa)")
    telefone_principal = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone Principal (Empresa)")

    # --- 3. FISCAL ---
    regime_tributario = models.CharField(max_length=20, choices=RegimeTributario.choices, blank=True, null=True, verbose_name="Regime Tributário")
    tipo_contribuinte = models.CharField(max_length=20, choices=TipoContribuinte.choices, blank=True, null=True, verbose_name="Tipo de Contribuinte")

    # --- 4. RELAÇÕES EXTERNAS ---
    distribuidora_padrao = models.ForeignKey(
        'tc_produtos.Fornecedor', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        verbose_name="Distribuidora Padrão",
        limit_choices_to={'e_distribuidor': True}
    )
    
    # --- 5. CONTROLE ---
    limite_credito = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Limite de Crédito")
    bloquear_faturamento = models.BooleanField(default=False, verbose_name="Bloquear Faturamento")
    etiquetas = models.ManyToManyField(Etiqueta, blank=True, verbose_name="Etiquetas")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Cliente (Conta)"
        verbose_name_plural = "Clientes (Contas)"

    def __str__(self):
        return self.razao_social

# Modelo para os Contatos (Pessoas específicas) associados a um Cliente
class Contato(models.Model):
    class PapelDecisao(models.TextChoices):
        DECISOR = 'decisor', _('Decisor')
        INFLUENCIADOR = 'influenciador', _('Influenciador')
        TECNICO = 'tecnico', _('Técnico')
        USUARIO = 'usuario', _('Usuário Final')
        OUTRO = 'outro', _('Outro')

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")
    primeiro_nome = models.CharField(max_length=100, verbose_name="Primeiro Nome")
    sobrenome = models.CharField(max_length=100, verbose_name="Sobrenome")
    email = models.EmailField(max_length=255, verbose_name="E-mail Pessoal/Trabalho")
    
    # CAMPOS ATUALIZADOS PARA SALVAMENTO
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone Fixo")
    celular = models.CharField(max_length=20, blank=True, null=True, verbose_name="Celular")
    departamento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Departamento")
    e_principal = models.BooleanField(default=False, verbose_name="Contato Principal")
    e_whatsapp = models.BooleanField(default=False, verbose_name="Possui WhatsApp")
    
    papel_na_decisao = models.CharField(max_length=20, choices=PapelDecisao.choices, blank=True, null=True, verbose_name="Papel na Decisão")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Contato"
        verbose_name_plural = "Contatos"

    def __str__(self):
        return f"{self.primeiro_nome} {self.sobrenome} ({self.cliente.razao_social})"

# Modelo para as Etapas do Pipeline de Vendas
class EtapaVenda(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome da Etapa")
    ordem = models.PositiveIntegerField(default=0, verbose_name="Ordem de Exibição")
    permite_proposta = models.BooleanField(
        default=False,
        verbose_name="Permite Criação de Proposta?",
        help_text="Marque se oportunidades nesta etapa podem ter novas propostas criadas."
    )
    e_etapa_ganha = models.BooleanField(
        default=False,
        verbose_name="É Etapa 'Ganha'?",
        help_text="Marque APENAS a(s) etapa(s) que representam uma venda concluída/ganha."
    )

    class Meta:
        verbose_name = "Etapa de Venda"
        verbose_name_plural = "Etapas de Vendas"
        ordering = ['ordem']

    def __str__(self):
        return self.nome

# Modelo para as Oportunidades de Negócio (Kanban)
class Oportunidade(models.Model):
    class TiposOportunidade(models.TextChoices):
        PROJETO = 'projeto', 'Projeto (Venda Única)'
        CONTRATO = 'contrato', 'Contrato (Recorrente)'
        
    # Status Operacional e Financeiro são definidos no módulo de OPERACOES/FINANCEIRO, 
    # mas são replicados aqui como campos para fins de CRM e relatórios rápidos.
    # Usaremos choices simples ou faremos um import mais limpo se necessário.
    class StatusOperacional(models.TextChoices): 
        AGUARDANDO = 'aguardando', 'Aguardando'
        INICIADO = 'iniciado', 'Iniciado'
        CONCLUIDO = 'concluido', 'Concluído'
        CANCELADO = 'cancelado', 'Cancelado'
    class StatusFinanceiro(models.TextChoices):
        AGUARDANDO = 'aguardando', 'Aguardando Faturamento'
        FATURADO = 'enviado', 'Faturado/Enviado' 
        PAGO = 'pago', 'Pago'
        ATRASADO = 'atrasado', 'Atrasado'
        CANCELADO = 'cancelado', 'Cancelado'

    nome = models.CharField(max_length=255, verbose_name="Nome da Oportunidade")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Vendedor Responsável")
    etapa = models.ForeignKey(EtapaVenda, on_delete=models.PROTECT, verbose_name="Etapa")
    valor_estimado = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Valor Estimado")
    data_fechamento_prevista = models.DateField(blank=True, null=True, verbose_name="Data de Fechamento Prevista")
    tipo_oportunidade = models.CharField(
        max_length=10, choices=TiposOportunidade.choices, default=TiposOportunidade.PROJETO, verbose_name="Tipo de Oportunidade"
    )

    # Acompanhamento Pós-Venda (CAMPOS DUPLICADOS AQUI PARA REDUÇÃO DE ACOPLAMENTO)
    data_fechamento_real = models.DateTimeField(blank=True, null=True, verbose_name="Data de Fechamento (Real)") 
    data_previsao_conclusao = models.DateField(blank=True, null=True, verbose_name="Previsão Conclusão (Operacional)")
    status_operacional = models.CharField(
        max_length=15, choices=StatusOperacional.choices, default=StatusOperacional.AGUARDANDO, verbose_name="Status Operacional"
    ) 
    status_financeiro = models.CharField(
        max_length=25, choices=StatusFinanceiro.choices, default=StatusFinanceiro.AGUARDANDO, verbose_name="Status Financeiro"
    ) 
    
    @property
    def contato_principal(self):
        return self.cliente.contato_set.filter(e_principal=True).first()
    # Propriedades de Status Pós-Venda (Lógica idêntica à anterior [1])
    @property
    def status_consolidado(self):
        op_status = self.status_operacional
        fin_status = self.status_financeiro
        if op_status == self.StatusOperacional.CANCELADO or fin_status == self.StatusFinanceiro.CANCELADO:
            return "Processo Cancelado"
        if op_status == self.StatusOperacional.CONCLUIDO and fin_status == self.StatusFinanceiro.PAGO:
            return "Processo Concluído"
        
        pending_items = []
        if op_status != self.StatusOperacional.CONCLUIDO:
            pending_items.append("Operacional")
        if fin_status != self.StatusFinanceiro.PAGO:
            pending_items.append("Financeiro")

        status_prefix = "Pendente: "
        if fin_status == self.StatusFinanceiro.ATRASADO:
            status_prefix = "Pendente (Pagto. Atrasado): "
        
        return status_prefix + ", ".join(pending_items)
        
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Oportunidade"
        verbose_name_plural = "Oportunidades"
        ordering = ['-data_fechamento_prevista']

    def save(self, *args, **kwargs):
        # Se a etapa for marcada como 'Ganha' e ainda não tiver data real, preenchemos agora
        if self.etapa.e_etapa_ganha and not self.data_fechamento_real:
            self.data_fechamento_real = timezone.now()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.nome

# Modelo para as Atividades (ligações, reuniões, tarefas)
class Atividade(models.Model):
    class TiposAtividade(models.TextChoices):
        LIGACAO = 'ligacao', 'Ligação'
        REUNIAO = 'reuniao', 'Reunião'
        TAREFA = 'tarefa', 'Tarefa'
        EMAIL = 'email', 'E-mail'
        OUTRO = 'outro', 'Outro'
        
    tipo_atividade = models.CharField(max_length=10, choices=TiposAtividade.choices, default=TiposAtividade.LIGACAO, verbose_name="Tipo de Atividade")
    assunto = models.CharField(max_length=255, verbose_name="Assunto")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição/Detalhes") # Adicionado para sincronizar com o Form
    data_hora = models.DateTimeField(verbose_name="Data e Hora")
    concluida = models.BooleanField(default=False, verbose_name="Concluída")
    
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Responsável") 
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Cliente")
    oportunidade = models.ForeignKey(Oportunidade, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Oportunidade")

    history = HistoricalRecords() # Mantendo seu padrão de histórico

    class Meta:
        verbose_name = "Atividade"
        verbose_name_plural = "Atividades"
        ordering = ['-data_hora'] # Invertido para mostrar as mais recentes primeiro

    def __str__(self):
        return f"{self.get_tipo_atividade_display()}: {self.assunto}"

# Modelo para as Propostas (inclui campos ROI)
class Proposta(models.Model):

    # Opções de Status
    STATUS_CHOICES = [
        ('elaboracao', 'Em Elaboração'),
        ('enviada', 'Enviada'),
        ('aceita', 'Aceita/Ganha'),
        ('recusada', 'Recusada'),
    ]

    id_proposta = models.CharField(max_length=20, unique=True, blank=True, editable=False, verbose_name="ID da Proposta")
    oportunidade = models.ForeignKey(Oportunidade, on_delete=models.CASCADE, verbose_name="Oportunidade")
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Criado por")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação") # Novo campo
    # Informações Técnicas/Comerciais
    entendimento_necessidade = models.TextField(verbose_name="Entendimento da Necessidade", blank=True, null=True)
    descricao_tecnica = models.TextField(verbose_name="Proposta Técnica", blank=True, null=True)
    descricao_comercial = models.TextField(verbose_name="Descrição da Proposta Comercial", blank=True, null=True)
    prazo_entrega = models.CharField(max_length=100, verbose_name="Prazo de Entrega", blank=True, null=True)
    validade_dias = models.CharField(max_length=100, verbose_name="Validade da Proposta", blank=True, null=True)
    vigencia_contrato = models.CharField(max_length=100, verbose_name="Vigência do Contrato", blank=True, null=True)
    forma_pagamento = models.TextField(verbose_name="Forma de Pagamento", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='elaboracao', verbose_name="Status da Proposta")

    # Relação com Contrato (No App CONTRATO)
    contrato = models.OneToOneField(
        'tc_contratos.Contrato', # Referência App CONTRATO
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='+'
    )
    
    # Campos de Custo e Receita (para ROI)
    custo_inicial_mo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Custo Inicial - Mão de Obra (R$)")
    custo_inicial_material = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Custo Inicial - Material/Licença (R$)")
    custo_inicial_outros = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Custo Inicial - Outros (R$)")
    custo_recorrente_mensal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Custo Recorrente Mensal (R$)")
    duracao_custo_meses = models.PositiveIntegerField(default=0, verbose_name="Duração Custo Recorrente (Meses)")
    receita_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Receita Inicial/Única (R$)")
    receita_mensal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Receita Recorrente Mensal (R$)")
    duracao_receita_meses = models.PositiveIntegerField(default=0, verbose_name="Duração Receita Recorrente (Meses)")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Proposta"
        verbose_name_plural = "Propostas"
        # ORDENAÇÃO: O sinal de menos '-' indica ordem decrescente (mais recente primeiro)
        ordering = ['-id_proposta']

    # 1. Frete
    valor_frete = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Valor do Frete (R$)")

    # 1.1 Desconto
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="(-) Valor do Desconto (R$)")

    # 2. Atualize a propriedade valor_total
    @property
    def valor_total(self):
        try:
            itens = self.itens.all()
        except AttributeError:
            try:
                itens = self.itemproposta_set.all()
            except AttributeError:
                return Decimal('0.00')
                
        total_itens = sum(item.total for item in itens)
        
        # Lógica Final: Itens + Frete - Desconto
        resultado = (total_itens + self.valor_frete) - self.valor_desconto
        return resultado.quantize(Decimal("0.01"))

    def save(self, *args, **kwargs):
        if not self.pk and not self.id_proposta:
            today = timezone.now()
            # CORREÇÃO DA LÓGICA: Formato AAAAMMDD (20251225)
            date_part = today.strftime('%Y%m%d')
            
            salesperson = self.criado_por
            if not salesperson:
                 raise ValueError("A proposta deve ter um usuário criador.")

            # Pega a inicial do username ou 'X' se estiver vazio
            initial_part = salesperson.username[0].upper() if salesperson.username else 'X'
            
            # Busca a última proposta criada HOJE para definir a sequência global
            PropostaModel = apps.get_model('tc_crm', 'Proposta')
            # Filtramos por id_proposta que começa com a data de hoje (AAAAMMDD)
            last_proposal_today = PropostaModel.objects.filter(
                id_proposta__startswith=date_part
            ).order_by('-id_proposta').first()

            next_sequence = 1
            if last_proposal_today:
                try:
                    # Captura os últimos 3 dígitos do código atual
                    last_sequence_str = last_proposal_today.id_proposta[-3:]
                    next_sequence = int(last_sequence_str) + 1
                except (ValueError, IndexError):
                    next_sequence = 1
            
            # Formata a sequência com 3 dígitos (ex: 001)
            sequence_part = str(next_sequence).zfill(3)
            
            # Monta o código final: 20251225D001
            self.id_proposta = f"{date_part}{initial_part}{sequence_part}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.id_proposta or f"Proposta (ID: {self.pk})"


# Modelo para os Itens da Proposta
class ItemProposta(models.Model):
   # proposta = models.ForeignKey(Proposta, on_delete=models.CASCADE, related_name='itens_proposta', verbose_name="Proposta")
    proposta = models.ForeignKey(Proposta, on_delete=models.CASCADE, related_name='itens')
    
    
    # Referência externa para o App PRODUTOS
    produto = models.ForeignKey(
        'tc_produtos.Produto', 
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Produto (Catálogo)"
    )
    # Referência externa para o App SERVICOS
    servico = models.ForeignKey(
        'tc_servicos.Servico', 
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Serviço (Catálogo)"
    )

    resumo_item = models.CharField(
        max_length=100, 
        verbose_name="Descrição (Resumo do Item)",
        help_text="Descrição curta (máx 100 char).",
        blank=True, null=True 
    ) 
    
    especificacao_tecnica = models.TextField(
        verbose_name="Especificação Técnica (Opcional)",
        help_text="Descrição longa do item.",
        blank=True, null=True
    ) 

    quantidade = models.PositiveIntegerField(default=1, verbose_name="Quantidade")
    preco_unitario = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name="Preço Unitário (R$)",
        help_text="Pode ser editado para o item."
    )
    
    @property
    def total(self):
        # Cálculo simples e direto para evitar erros de agregação
        preco = self.preco_unitario or Decimal('0.00')
        qtd = self.quantidade or 0
        return (Decimal(qtd) * preco).quantize(Decimal("0.01"))

    class Meta:
        verbose_name = "Item da Proposta"
        verbose_name_plural = "Itens da Proposta"

    def __str__(self):
        return self.resumo_item or "Item sem Resumo"

class Fornecedor(models.Model):
    razao_social = models.CharField(max_length=255, verbose_name="Razão Social")
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    # ... outros campos legados que você já tenha
    
    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self):
        return self.razao_social

class Produto(models.Model):
    nome = models.CharField(max_length=255, verbose_name="Nome do Produto")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return self.nome

class MetaMensal(models.Model):
    MESES_CHOICES = [
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro'),
    ]

    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='metas',
        limit_choices_to={'is_active': True},
        null=True, blank=True,
        help_text="Deixe em branco para Meta Global da Empresa"
    )
    ano = models.PositiveIntegerField(default=2026)
    mes = models.PositiveIntegerField(choices=MESES_CHOICES)
    valor_objetivo = models.DecimalField(max_digits=12, decimal_places=2)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Meta Mensal"
        verbose_name_plural = "Metas Mensais"
        unique_together = ['vendedor', 'ano', 'mes'] # Impede duplicidade

    def __str__(self):
        tipo = self.vendedor.get_full_name() if self.vendedor else "GLOBAL"
        return f"{tipo} - {self.get_mes_display()}/{self.ano}: R$ {self.valor_objetivo}"