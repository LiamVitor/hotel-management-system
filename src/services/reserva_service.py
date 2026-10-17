from database.conexao import obter_conexao
from src.models.reserva import Reserva
from src.repositories.hospede_repository import HospedeRepository
from src.repositories.quarto_repository import QuartoRepository
from src.repositories.reserva_repository import ReservaRepository
from src.services import reserva_regras as regras
from src.services.erros import ErroNegocio
from src.utils.constantes import (QUARTO_DISPONIVEL, QUARTO_MANUTENCAO, QUARTO_OCUPADO,
                                  RESERVA_CONFIRMADA, RESERVA_FINALIZADA, RESERVA_HOSPEDADA)


class ReservaService:
    def __init__(self, repo=None, quarto_repo=None, hospede_repo=None):
        self.repo = repo or ReservaRepository()
        self.quarto_repo = quarto_repo or QuartoRepository()
        self.hospede_repo = hospede_repo or HospedeRepository()

    # ---------- consultas ----------
    def listar(self):
        return self.repo.listar()

    def buscar_por_id(self, reserva_id):
        return self.repo.buscar_por_id(reserva_id)

    def tem_conflito(self, quarto_id, entrada, saida):
        return bool(self.repo.listar_conflitantes(quarto_id, entrada, saida))

    # ---------- criação ----------
    def criar_reserva(self, hospede_id, quarto_id, entrada, saida, numero_hospedes):
        try:
            regras.validar_periodo(entrada, saida)
        except ValueError as erro:
            raise ErroNegocio(str(erro))

        if self.hospede_repo.buscar_por_id(hospede_id) is None:
            raise ErroNegocio("Hóspede não encontrado.")
        quarto = self.quarto_repo.buscar_por_id(quarto_id)
        if quarto is None:
            raise ErroNegocio("Quarto não encontrado.")
        if quarto.situacao == QUARTO_MANUTENCAO:
            raise ErroNegocio("Quarto em manutenção.")
        if self.tem_conflito(quarto_id, entrada, saida):
            raise ErroNegocio("Quarto já reservado neste período.")
        try:
            regras.validar_capacidade(quarto, numero_hospedes)
        except ValueError as erro:
            raise ErroNegocio(str(erro))

        diarias = regras.calcular_diarias(entrada, saida)
        reserva = Reserva(
            hospede_id=hospede_id, quarto_id=quarto_id,
            data_entrada=entrada, data_saida=saida,
            valor_diaria=quarto.preco_diaria,
            valor_total=regras.calcular_total(diarias, quarto.preco_diaria),
            situacao=RESERVA_CONFIRMADA,
        )
        with obter_conexao() as conexao:
            return self.repo.criar(reserva, conexao=conexao)

    # ---------- mudanças de situação ----------
    def cancelar(self, reserva_id):
        reserva = self._obter(reserva_id)
        if not regras.pode_cancelar(reserva):
            raise ErroNegocio("Só é possível cancelar reservas confirmadas, antes do check-in.")
        self.repo.cancelar(reserva_id)

    def fazer_checkin(self, reserva_id):
        reserva = self._obter(reserva_id)
        if not regras.pode_fazer_checkin(reserva):
            raise ErroNegocio("O check-in só é permitido para reservas confirmadas.")
        return self._trocar_situacao(reserva, RESERVA_HOSPEDADA, QUARTO_OCUPADO)

    def fazer_checkout(self, reserva_id):
        reserva = self._obter(reserva_id)
        if reserva.situacao != RESERVA_HOSPEDADA:
            raise ErroNegocio("O check-out só é permitido para hóspedes hospedados.")
        return self._trocar_situacao(reserva, RESERVA_FINALIZADA, QUARTO_DISPONIVEL)

    # ---------- internos ----------
    def _obter(self, reserva_id):
        reserva = self.repo.buscar_por_id(reserva_id)
        if reserva is None:
            raise ErroNegocio("Reserva não encontrada.")
        return reserva

    def _trocar_situacao(self, reserva, situacao_reserva, situacao_quarto):
        """Atualiza reserva e quarto na mesma transação: ou muda os dois ou nenhum."""
        reserva.situacao = situacao_reserva
        with obter_conexao() as conexao:
            self.repo.atualizar(reserva, conexao=conexao)
            self.quarto_repo.atualizar_situacao(reserva.quarto_id, situacao_quarto,
                                                conexao=conexao)
        return reserva
