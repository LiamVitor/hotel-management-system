from datetime import date

from src.models.checkin import PainelCheckin
from src.services import checkin_regras as regras
from src.services.hospede_service import HospedeService
from src.services.quarto_service import QuartoService
from src.services.reserva_service import ReservaService
from src.utils.constantes import MOVIMENTO_CHECKIN
from src.utils.sessao import Sessao


class CheckinCheckoutService:
    """Monta o painel da tela de check-in / check-out a partir das reservas.

    Fazer o check-in e o check-out continua em `ReservaService` (fazer_checkin / fazer_checkout);
    aqui só ficam as consultas: quem deve chegar, quem está hospedado e o que já foi feito hoje.
    """

    def __init__(self, reservas=None, hospedes=None, quartos=None):
        self.reservas = reservas or ReservaService()
        self.hospedes = hospedes or HospedeService()
        self.quartos = quartos or QuartoService()

    def painel(self, termo="", hoje=None):
        Sessao.exigir("reservas.checkin")
        hoje = hoje or date.today()
        todas = self.reservas.listar()
        chegadas, hospedados = regras.chegadas(todas, hoje), regras.hospedados(todas)
        painel = PainelCheckin(
            hoje=hoje,
            chegadas_hoje=sum(1 for r in chegadas if r.data_entrada == hoje),
            chegadas_atrasadas=sum(1 for r in chegadas if r.data_entrada < hoje),
            saidas_hoje=sum(1 for r in hospedados if r.data_saida == hoje),
            saidas_atrasadas=sum(1 for r in hospedados if r.data_saida < hoje),
            total_hospedados=len(hospedados))

        if (termo or "").strip():
            hospedes = {h.id: h for h in self.hospedes.listar()}
            quartos = {q.id: q for q in self.quartos.listar()}
            chegadas = regras.filtrar(chegadas, termo, hospedes, quartos)
            hospedados = regras.filtrar(hospedados, termo, hospedes, quartos)
        painel.chegadas, painel.hospedados = chegadas, hospedados

        painel.movimentos = regras.movimentos_do_dia(todas, hoje)
        nomes = self.reservas.responsaveis([m.reserva for m in painel.movimentos])
        for m in painel.movimentos:
            usuario = m.reserva.checkin_por if m.tipo == MOVIMENTO_CHECKIN else m.reserva.checkout_por
            m.responsavel = nomes.get(usuario, "—")
        return painel
