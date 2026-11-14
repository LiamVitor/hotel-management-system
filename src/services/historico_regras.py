"""Regras do histórico de hospedagem de um hóspede (funções puras)."""
from src.models.historico_hospedagem import ItemHistorico
from src.services.pagamento_regras import arredondar
from src.utils.constantes import (RESERVA_CANCELADA, RESERVA_CONFIRMADA, RESERVA_FINALIZADA,
                                  RESERVA_HOSPEDADA, RESERVA_NO_SHOW)

# situações em que o hóspede chegou a ocupar o quarto
SITUACOES_DE_HOSPEDAGEM = (RESERVA_HOSPEDADA, RESERVA_FINALIZADA)


def montar_item(reserva, quarto, valor_pago):
    """ItemHistorico de uma reserva (quarto pode ser None se o cadastro sumiu)."""
    return ItemHistorico(
        reserva_id=reserva.id, quarto_id=reserva.quarto_id,
        quarto=quarto.numero if quarto else "—", tipo_quarto=quarto.tipo if quarto else "",
        data_entrada=reserva.data_entrada, data_saida=reserva.data_saida,
        noites=(reserva.data_saida - reserva.data_entrada).days,
        valor_total=arredondar(reserva.valor_total), valor_pago=arredondar(valor_pago),
        situacao=reserva.situacao, hospedagem=reserva.situacao in SITUACOES_DE_HOSPEDAGEM,
        checkin_em=reserva.checkin_em, checkout_em=reserva.checkout_em)


def resumir(itens):
    """Números do histórico inteiro do hóspede.

    hospedagens: reservas em que ele chegou a se hospedar (Hospedada ou Finalizada);
    reservas: todas as reservas; noites: soma das noites das hospedagens;
    total_pago: tudo que ele pagou, já sem os reembolsos (inclui o que ficou retido em
    cancelamento ou no-show); quartos_utilizados: números dos quartos das hospedagens.
    """
    hospedagens = [i for i in itens if i.hospedagem]
    return {
        "hospedagens": len(hospedagens),
        "reservas": len(itens),
        "futuras": sum(i.situacao == RESERVA_CONFIRMADA for i in itens),
        "canceladas": sum(i.situacao == RESERVA_CANCELADA for i in itens),
        "no_shows": sum(i.situacao == RESERVA_NO_SHOW for i in itens),
        "noites": sum(i.noites for i in hospedagens),
        "total_pago": arredondar(sum(i.valor_pago for i in itens)),
        "quartos_utilizados": sorted({i.quarto for i in hospedagens}),
        "ultima_hospedagem": max((i.data_entrada for i in hospedagens), default=None),
    }
