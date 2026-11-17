"""Regras de negócio dos bloqueios de quarto (funções puras, sem banco e sem interface)."""
from datetime import datetime, time

from src.services.reserva_regras import STATUS_QUE_BLOQUEIAM_QUARTO
from src.utils.constantes import BLOQUEIO_AGENDADO, BLOQUEIO_EM_ANDAMENTO, BLOQUEIO_ENCERRADO


def periodos_se_sobrepoem(inicio_a, fim_a, inicio_b, fim_b):
    """Quem termina exatamente quando o outro começa não conta como conflito."""
    return inicio_a < fim_b and fim_a > inicio_b


def intervalo_da_reserva(entrada, saida):
    """A reserva (datas) como intervalo de data e hora: da meia-noite da entrada à da saída.

    É a forma de comparar uma reserva com um bloqueio, que tem hora. Na prática, o bloqueio
    conflita com a reserva se tocar qualquer dia em que o hóspede dorme no quarto; o dia da
    saída, depois da meia-noite, fica de fora.
    """
    return datetime.combine(entrada, time.min), datetime.combine(saida, time.min)


def situacao_do_bloqueio(bloqueio, agora):
    """Agendado (ainda não começou), Em andamento ou Encerrado."""
    if agora < bloqueio.inicio:
        return BLOQUEIO_AGENDADO
    if agora < bloqueio.fim:
        return BLOQUEIO_EM_ANDAMENTO
    return BLOQUEIO_ENCERRADO


def impedimento_do_periodo(inicio, fim, agora):
    """Texto explicando por que o período é inválido para um novo bloqueio, ou None se serve."""
    if fim <= inicio:
        return "O término do bloqueio deve ser posterior ao início."
    if fim <= agora:
        return "O término do bloqueio deve ser no futuro."
    return None


def reservas_em_conflito(reservas, quarto_id, inicio, fim):
    """Reservas ativas (confirmadas ou hospedadas) do quarto que se sobrepõem ao período."""
    return [r for r in reservas
            if r.quarto_id == quarto_id and r.situacao in STATUS_QUE_BLOQUEIAM_QUARTO
            and periodos_se_sobrepoem(inicio, fim, *intervalo_da_reserva(r.data_entrada,
                                                                         r.data_saida))]
