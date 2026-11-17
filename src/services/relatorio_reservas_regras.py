"""Regras dos relatórios de reservas por período e de check-ins/check-outs (funções puras)."""
from src.services.pagamento_regras import arredondar
from src.utils.constantes import (MOVIMENTO_CHECKIN, MOVIMENTO_CHECKOUT, RESERVA_CANCELADA,
                                  RESERVA_NO_SHOW)

# Como o check-in/check-out real se compara com a data prevista da reserva
NA_DATA = "Na data prevista"
ANTECIPADO = "Antecipado"
DEPOIS = "Após a data prevista"


def totalizar_reservas(reservas):
    """Somas da lista de reservas.

    'Valor reservado' e 'noites' contam só as reservas que ocupam (ou ocuparam) o quarto, a mesma
    base do demonstrativo de receitas; canceladas e no-shows aparecem na contagem à parte.
    """
    ativas = [r for r in reservas if r.situacao not in (RESERVA_CANCELADA, RESERVA_NO_SHOW)]
    return {
        "reservas": len(reservas),
        "valor_reservado": arredondar(sum(r.valor_total for r in ativas)),
        "noites": sum(r.noites for r in ativas),
        "valor_pago": arredondar(sum(r.valor_pago for r in reservas)),
        "canceladas": sum(r.situacao == RESERVA_CANCELADA for r in reservas),
        "no_shows": sum(r.situacao == RESERVA_NO_SHOW for r in reservas),
    }


def situacao_do_horario(movimento):
    """Compara o DIA em que o check-in/check-out aconteceu com o dia previsto na reserva."""
    dia = movimento.data_hora.date()
    if dia == movimento.data_prevista:
        return NA_DATA
    return ANTECIPADO if dia < movimento.data_prevista else DEPOIS


def totalizar_movimentos(movimentos):
    """Quantos check-ins e check-outs, e quantos aconteceram fora da data prevista."""
    checkins = [m for m in movimentos if m.tipo == MOVIMENTO_CHECKIN]
    checkouts = [m for m in movimentos if m.tipo == MOVIMENTO_CHECKOUT]
    return {
        "checkins": len(checkins),
        "checkouts": len(checkouts),
        "checkins_fora_da_data": sum(situacao_do_horario(m) != NA_DATA for m in checkins),
        "checkouts_fora_da_data": sum(situacao_do_horario(m) != NA_DATA for m in checkouts),
    }
