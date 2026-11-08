import math
from datetime import datetime

from src.models.pagamento import Pagamento
from src.repositories.pagamento_repository import PagamentoRepository
from src.repositories.reserva_repository import ReservaRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.services import pagamento_regras as regras
from src.services.erros import ErroNegocio
from src.utils.constantes import FORMAS_PAGAMENTO, PAGAMENTO_NORMAL, RESERVA_CANCELADA
from src.utils.formatacao import formatar_moeda
from src.utils.sessao import Sessao


class PagamentoService:
    def __init__(self, repo=None, reserva_repo=None, usuario_repo=None):
        self.repo = repo or PagamentoRepository()
        self.reserva_repo = reserva_repo or ReservaRepository()
        self.usuario_repo = usuario_repo or UsuarioRepository()

    # ---------- consultas ----------
    def listar_por_reserva(self, reserva_id):
        """Histórico de pagamentos da reserva, do mais antigo para o mais recente."""
        return self.repo.listar_por_reserva(reserva_id)

    def historico(self, reserva_id):
        """Lista de (Pagamento, nome de quem lançou), do mais antigo para o mais recente.

        O nome é buscado direto no repositório de usuários porque listar usuários é
        restrito ao administrador, mas qualquer perfil precisa ver quem lançou.
        """
        nomes = {}
        resultado = []
        for pagamento in self.repo.listar_por_reserva(reserva_id):
            if pagamento.usuario_id not in nomes:
                usuario = self.usuario_repo.buscar_por_id(pagamento.usuario_id)
                nomes[pagamento.usuario_id] = usuario.nome if usuario else None
            resultado.append((pagamento, nomes[pagamento.usuario_id]))
        return resultado

    def resumo(self, reserva_id):
        """Total, quanto já foi pago, saldo pendente e situação (Pendente/Parcial/Pago)."""
        reserva = self._obter_reserva(reserva_id)
        return regras.resumir(reserva.valor_total, self.repo.listar_por_reserva(reserva_id))

    def totais_por_reserva(self):
        """{reserva_id: total pago} de todas as reservas, em uma consulta só."""
        return self.repo.totais_por_reserva()

    # ---------- lançamento ----------
    def registrar(self, reserva_id, valor, forma, data_hora=None):
        """Lança um pagamento (parcial ou integral) em uma reserva.

        O responsável é sempre o usuário logado e a data/hora é a do momento do
        lançamento. O valor não pode passar do saldo pendente.
        """
        Sessao.exigir("pagamentos.registrar")
        reserva = self._obter_reserva(reserva_id)
        if reserva.situacao == RESERVA_CANCELADA:
            raise ErroNegocio("Não é possível registrar pagamento em uma reserva cancelada.")

        try:
            valor = regras.arredondar(float(valor))
        except (TypeError, ValueError):
            raise ErroNegocio("Informe um valor válido para o pagamento.")
        if not math.isfinite(valor) or valor <= 0:
            raise ErroNegocio("O valor do pagamento deve ser maior que zero.")
        if forma not in FORMAS_PAGAMENTO:
            raise ErroNegocio("Selecione a forma de pagamento.")

        saldo = self.resumo(reserva_id).saldo
        if saldo <= 0:
            raise ErroNegocio("Esta reserva já está quitada.")
        if valor > saldo:
            raise ErroNegocio(f"O valor excede o saldo pendente de {formatar_moeda(saldo)}.")

        return self.repo.criar(Pagamento(
            reserva_id=reserva_id, valor=valor, forma=forma, tipo=PAGAMENTO_NORMAL,
            usuario_id=Sessao.usuario.id, data_hora=data_hora or datetime.now()))

    # ---------- internos ----------
    def _obter_reserva(self, reserva_id):
        reserva = self.reserva_repo.buscar_por_id(reserva_id)
        if reserva is None:
            raise ErroNegocio("Reserva não encontrada.")
        return reserva
