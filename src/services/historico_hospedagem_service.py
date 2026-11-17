from src.repositories.hospede_repository import HospedeRepository
from src.repositories.pagamento_repository import PagamentoRepository
from src.repositories.quarto_repository import QuartoRepository
from src.repositories.reserva_repository import ReservaRepository
from src.services import historico_regras as regras
from src.services.erros import ErroNegocio
from src.models.historico_hospedagem import HistoricoHospedagem
from src.utils.constantes import SITUACOES_RESERVA
from src.utils.sessao import Sessao


class HistoricoHospedagemService:
    """Histórico de reservas e hospedagens de um hóspede específico."""

    def __init__(self, hospede_repo=None, reserva_repo=None, quarto_repo=None,
                 pagamento_repo=None):
        self.hospede_repo = hospede_repo or HospedeRepository()
        self.reserva_repo = reserva_repo or ReservaRepository()
        self.quarto_repo = quarto_repo or QuartoRepository()
        self.pagamento_repo = pagamento_repo or PagamentoRepository()

    def historico(self, hospede_id, situacao=""):
        """Reservas do hóspede (mais recente primeiro) e o resumo do histórico inteiro.

        situacao: se informada (Confirmada, Hospedada, Finalizada, Cancelada ou Não compareceu),
        só a lista de reservas é filtrada; o resumo continua sendo do histórico completo.
        """
        Sessao.exigir("hospedes.ver")
        hospede = self.hospede_repo.buscar_por_id(hospede_id)
        if hospede is None:
            raise ErroNegocio("Hóspede não encontrado.")
        if situacao and situacao not in SITUACOES_RESERVA:
            raise ErroNegocio("Situação inválida.")

        reservas = sorted(self.reserva_repo.listar_por_hospede(hospede_id),
                          key=lambda r: (r.data_entrada, r.id), reverse=True)
        quartos = {q.id: q for q in self.quarto_repo.listar()}
        pagos = self.pagamento_repo.totais_por_hospede(hospede_id)
        todos = [regras.montar_item(r, quartos.get(r.quarto_id), pagos.get(r.id, 0.0))
                 for r in reservas]
        itens = [i for i in todos if not situacao or i.situacao == situacao]
        return HistoricoHospedagem(hospede=hospede, itens=itens, resumo=regras.resumir(todos))
