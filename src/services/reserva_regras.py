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
