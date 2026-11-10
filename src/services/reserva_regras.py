"""Regras de negócio das reservas (funções puras, sem banco e sem interface)."""
from src.utils.constantes import RESERVA_CONFIRMADA, RESERVA_HOSPEDADA

STATUS_QUE_BLOQUEIAM_QUARTO = (RESERVA_CONFIRMADA, RESERVA_HOSPEDADA)


def calcular_diarias(entrada, saida):
    return (saida - entrada).days


def calcular_total(diarias, valor_diaria):
    return diarias * valor_diaria


def validar_periodo(entrada, saida):
    if saida <= entrada:
        raise ValueError("A data de saída deve ser posterior à data de entrada.")


def periodos_se_sobrepoem(entrada_a, saida_a, entrada_b, saida_b):
    """O dia de troca (saída de um = entrada do outro) não conta como conflito."""
    return entrada_a < saida_b and saida_a > entrada_b


def existe_conflito(reservas, quarto_id, entrada, saida, ignorar_id=None):
    for r in reservas:
        if r.quarto_id != quarto_id or r.id == ignorar_id:
            continue
        if r.situacao not in STATUS_QUE_BLOQUEIAM_QUARTO:
            continue
        if periodos_se_sobrepoem(entrada, saida, r.data_entrada, r.data_saida):
            return True
    return False


def validar_capacidade(quarto, numero_hospedes):
    if numero_hospedes < 1:
        raise ValueError("Informe ao menos 1 hóspede.")
    if numero_hospedes > quarto.capacidade:
        raise ValueError(f"O quarto comporta no máximo {quarto.capacidade} hóspede(s).")


def pode_fazer_checkin(reserva):
    return reserva.situacao == RESERVA_CONFIRMADA


def pode_cancelar(reserva):
    """Cancelamento só antes do check-in."""
    return reserva.situacao == RESERVA_CONFIRMADA


def impedimento_no_show(reserva, hoje):
    """Texto explicando por que a reserva não pode ser marcada como no-show, ou None se pode.

    Só vale para reserva confirmada (sem check-in) e a partir da data de entrada prevista:
    antes disso o hóspede ainda pode chegar.
    """
    if reserva.situacao != RESERVA_CONFIRMADA:
        return "Só é possível marcar como 'Não compareceu' reservas confirmadas, sem check-in."
    if hoje < reserva.data_entrada:
        return (f"O hóspede ainda não passou da data de entrada prevista "
                f"({reserva.data_entrada:%d/%m/%Y}). Se ele desistiu, cancele a reserva.")
    return None


def pode_marcar_no_show(reserva, hoje):
    return impedimento_no_show(reserva, hoje) is None


def dias_de_diferenca_entrada(reserva):
    """Dias entre a entrada real e a prevista: positivo = chegou depois, negativo = antes.
    None se o check-in ainda não foi registrado."""
    if reserva.checkin_em is None:
        return None
    return (reserva.checkin_em.date() - reserva.data_entrada).days


def dias_de_diferenca_saida(reserva):
    """Dias entre a saída real e a prevista: positivo = saiu depois, negativo = antes.
    None se o check-out ainda não foi registrado."""
    if reserva.checkout_em is None:
        return None
    return (reserva.checkout_em.date() - reserva.data_saida).days


def noites_reais(reserva):
    """Noites que o hóspede realmente ficou (do dia do check-in ao do check-out).
    None se faltar o check-in ou o check-out."""
    if reserva.checkin_em is None or reserva.checkout_em is None:
        return None
    return max((reserva.checkout_em.date() - reserva.checkin_em.date()).days, 0)
