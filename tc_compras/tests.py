from django.test import TestCase
from django.apps import apps
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal
import datetime

# Modelos que vamos testar e com os quais interagimos (assumindo a estrutura modular)
# Usamos apps.get_model para garantir que os modelos sejam carregados dinamicamente
RecebimentoItem = apps.get_model('compras', 'RecebimentoItem')
ItemPedidoCompra = apps.get_model('compras', 'ItemPedidoCompra')
PedidoCompra = apps.get_model('compras', 'PedidoCompra')
RequisicaoCompra = apps.get_model('compras', 'RequisicaoCompra')
CentroCusto = apps.get_model('compras', 'CentroCusto')

Produto = apps.get_model('produtos', 'Produto')
Fornecedor = apps.get_model('produtos', 'Fornecedor')

ItemEstoque = apps.get_model('estoque', 'ItemEstoque')
MovimentacaoEstoque = apps.get_model('estoque', 'MovimentacaoEstoque')

User = get_user_model() # Obtém o modelo de usuário do CORE

class RecebimentoEstoqueIntegrationTest(TestCase):
    """
    Testes de integração para garantir que o RecebimentoItem atualize
    o saldo de estoque (ItemEstoque) e o status do pedido de compra.
    """
    @classmethod
    def setUpTestData(cls):
        # 1. Configuração de Usuários e Entidades Base
        cls.usuario_estoque = User.objects.create_user(
            username='estoquista', 
            email='estoque@erp.com', 
            password='password'
        )
        cls.fornecedor = Fornecedor.objects.create(
            razao_social='Tech Suprimentos',
            cnpj='00.000.000/0001-00'
        )
        cls.produto_consumo = Produto.objects.create(
            nome='Material de Escritório',
            tipo_produto=Produto.TipoProduto.ESTOQUE_PROPRIO,
            custo_padrao=Decimal('10.00')
        )
        cls.centrocusto = CentroCusto.objects.create(nome='Administrativo', codigo='ADM')
        
        # 2. Criação de ItemEstoque Inicial (Saldo ZERO)
        cls.item_estoque = ItemEstoque.objects.create(
            produto=cls.produto_consumo,
            quantidade=0,
            localizacao='Prateleira 1A'
        )

        # 3. Criação de Pedido de Compra (PO) e ItemPedidoCompra
        cls.requisicao = RequisicaoCompra.objects.create(
            solicitante=cls.usuario_estoque,
            centro_custo=cls.centrocusto,
            status=RequisicaoCompra.StatusRequisicao.APROVADA
        )
        cls.pedido_compra = PedidoCompra.objects.create(
            fornecedor=cls.fornecedor,
            requisicao_origem=cls.requisicao,
            status=PedidoCompra.StatusPedido.ABERTO,
            data_emissao=datetime.date.today()
        )
        cls.item_pedido = ItemPedidoCompra.objects.create(
            pedido_compra=cls.pedido_compra,
            produto=cls.produto_consumo,
            descricao_item='Caixa de Canetas',
            quantidade_pedida=20,
            preco_unitario=Decimal('9.50')
        )

    def test_recebimento_parcial_atualiza_saldo_e_item_pedido(self):
        """
        Testa o recebimento de uma quantidade parcial. O saldo de estoque deve
        aumentar, e o saldo do ItemPedido deve refletir o recebimento.
        """
        quantidade_receber = 10
        
        recebimento = RecebimentoItem.objects.create(
            item_pedido=self.item_pedido,
            quantidade_recebida=quantidade_receber,
            recebedor=self.usuario_estoque
        )

        # Recarrega os objetos para verificar as mudanças no banco de dados
        self.item_estoque.refresh_from_db()
        self.item_pedido.refresh_from_db()

        # 1. Assert: Saldo de Estoque Atualizado
        self.assertEqual(self.item_estoque.quantidade, quantidade_receber)
        
        # 2. Assert: ItemPedidoCompra Atualizado
        self.assertEqual(self.item_pedido.quantidade_recebida, quantidade_receber)
        
        # 3. Assert: Registro de Movimentação Criado
        movimentacao_entrada = MovimentacaoEstoque.objects.get(
            item_estoque=self.item_estoque,
            tipo=MovimentacaoEstoque.TipoMovimentacao.ENTRADA
        )
        self.assertEqual(movimentacao_entrada.quantidade, quantidade_receber)
        
        # 4. Assert: Status do Pedido de Compra permanece ABERTO (ainda não está TOTALMENTE recebido)
        self.assertEqual(self.pedido_compra.status, PedidoCompra.StatusPedido.ABERTO)


    def test_recebimento_total_atualiza_status_do_pedido(self):
        """
        Testa o recebimento da quantidade restante. O status do PedidoCompra
        deve mudar para RECEBIDO_TOTAL.
        """
        # Recebimento parcial (10)
        RecebimentoItem.objects.create(
            item_pedido=self.item_pedido,
            quantidade_recebida=10,
            recebedor=self.usuario_estoque
        )

        # Recebimento restante (10)
        RecebimentoItem.objects.create(
            item_pedido=self.item_pedido,
            quantidade_recebida=10,
            recebedor=self.usuario_estoque
        )

        self.item_estoque.refresh_from_db()
        self.item_pedido.refresh_from_db()
        self.pedido_compra.refresh_from_db()
        
        # 1. Assert: Saldo Total de Estoque
        self.assertEqual(self.item_estoque.quantidade, 20)
        
        # 2. Assert: ItemPedido totalmente recebido
        self.assertEqual(self.item_pedido.quantidade_recebida, 20)

        # 3. Assert: Status do Pedido de Compra atualizado para RECEBIDO
        self.assertEqual(self.pedido_compra.status, PedidoCompra.StatusPedido.RECEBIDO_TOTAL)


    def test_recebimento_com_quantidade_excessiva_falha_atomicamente(self):
        """
        Tenta receber uma quantidade maior do que a pedida. Deve falhar com
        ValidationError e não deve alterar o estoque nem o item do pedido.
        """
        # Quantidade total pedida é 20.
        quantidade_excessiva = 25
        
        # Salva o saldo inicial para verificar que não houve alteração
        saldo_estoque_inicial = self.item_estoque.quantidade 
        recebido_item_pedido_inicial = self.item_pedido.quantidade_recebida
        
        # O teste deve garantir que o ValidationError é levantado
        with self.assertRaises(ValidationError) as cm:
            RecebimentoItem.objects.create(
                item_pedido=self.item_pedido,
                quantidade_recebida=quantidade_excessiva,
                recebedor=self.usuario_estoque
            )
            
        # 1. Assert: Verifica se a mensagem de erro é a esperada
        self.assertIn("excede o saldo pendente", str(cm.exception))

        # 2. Assert: Estado inalterado (rollback garantido pelo @transaction.atomic)
        self.item_estoque.refresh_from_db()
        self.item_pedido.refresh_from_db()
        
        self.assertEqual(self.item_estoque.quantidade, saldo_estoque_inicial)
        self.assertEqual(self.item_pedido.quantidade_recebida, recebido_item_pedido_inicial)
        
        # 3. Assert: Nenhuma Movimentação foi criada
        self.assertEqual(MovimentacaoEstoque.objects.count(), 0)

    
    def test_recebimento_apos_totalmente_recebido(self):
        """
        Tenta receber itens de um pedido que já foi totalmente recebido.
        Deve falhar.
        """
        # Recebe o total (20)
        RecebimentoItem.objects.create(
            item_pedido=self.item_pedido,
            quantidade_recebida=20,
            recebedor=self.usuario_estoque
        )

        # Tenta receber mais 1
        with self.assertRaises(ValidationError) as cm:
            RecebimentoItem.objects.create(
                item_pedido=self.item_pedido,
                quantidade_recebida=1,
                recebedor=self.usuario_estoque
            )
        
        # Assert: A quantidade pendente deve ser 0
        self.assertIn("excede o saldo pendente (0)", str(cm.exception))