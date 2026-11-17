from datetime import date

import pytest

from src.models.quarto import Quarto
from src.models.reserva import Reserva
from src.services import reserva_regras as regras
from src.services.relatorios import ocupacao_por_dia, resumo_periodo
from src.utils.constantes import RESERVA_CANCELADA, RESERVA_CONFIRMADA, RESERVA_HOSPEDADA


def reserva(id, quarto_id, entrada, saida, situacao=RESERVA_CONFIRMADA):
    return Reserva(id=id, hospede_id=1, quarto_id=quarto_id, data_entrada=entrada,
                   data_saida=saida, valor_diaria=100.0,
                   valor_total=100.0 * (saida - entrada).days, situacao=situacao)


def test_total_e_diarias():
    diarias = regras.calcular_diarias(date(2026, 10, 20), date(2026, 10, 23))
    assert diarias == 3
    assert regras.calcular_total(diarias, 180.0) == 540.0


def test_saida_deve_ser_posterior_a_entrada():
    with pytest.raises(ValueError):
        regras.validar_periodo(date(2026, 10, 22), date(2026, 10, 22))
    with pytest.raises(ValueError):
        regras.validar_periodo(date(2026, 10, 22), date(2026, 10, 20))


def test_conflito_de_periodo():
    existentes = [reserva(1, 1, date(2026, 10, 20), date(2026, 10, 25))]
    assert regras.existe_conflito(existentes, 1, date(2026, 10, 23), date(2026, 10, 27))
    assert not regras.existe_conflito(existentes, 2, date(2026, 10, 23), date(2026, 10, 27))


def test_dia_de_troca_nao_e_conflito():
    existentes = [reserva(1, 1, date(2026, 10, 20), date(2026, 10, 25))]
    assert not regras.existe_conflito(existentes, 1, date(2026, 10, 25), date(2026, 10, 27))


def test_cancelada_nao_bloqueia_e_hospedada_bloqueia():
    cancelada = [reserva(1, 1, date(2026, 10, 20), date(2026, 10, 25), RESERVA_CANCELADA)]
    hospedada = [reserva(1, 1, date(2026, 10, 20), date(2026, 10, 25), RESERVA_HOSPEDADA)]
    assert not regras.existe_conflito(cancelada, 1, date(2026, 10, 21), date(2026, 10, 23))
    assert regras.existe_conflito(hospedada, 1, date(2026, 10, 21), date(2026, 10, 23))


def test_ignorar_a_propria_reserva_ao_editar():
    existentes = [reserva(1, 1, date(2026, 10, 20), date(2026, 10, 25))]
    assert not regras.existe_conflito(existentes, 1, date(2026, 10, 21), date(2026, 10, 24), ignorar_id=1)


def test_capacidade():
    quarto = Quarto(numero="101", tipo="Casal", capacidade=2, preco_diaria=180.0, id=1)
    regras.validar_capacidade(quarto, 2)
    with pytest.raises(ValueError):
        regras.validar_capacidade(quarto, 3)
    with pytest.raises(ValueError):
        regras.validar_capacidade(quarto, 0)


def test_checkin_e_cancelamento_so_para_confirmadas():
    confirmada = reserva(1, 1, date(2026, 10, 20), date(2026, 10, 22))
    hospedada = reserva(2, 1, date(2026, 10, 20), date(2026, 10, 22), RESERVA_HOSPEDADA)
    assert regras.pode_fazer_checkin(confirmada) and regras.pode_cancelar(confirmada)
    assert not regras.pode_fazer_checkin(hospedada) and not regras.pode_cancelar(hospedada)


def test_relatorio_ocupacao_e_faturamento():
    quartos = [Quarto(numero=str(i), tipo="Casal", capacidade=2, preco_diaria=100.0, id=i)
               for i in (1, 2)]
    reservas = [reserva(1, 1, date(2026, 10, 20), date(2026, 10, 22)),
                reserva(2, 2, date(2026, 10, 21), date(2026, 10, 22), RESERVA_CANCELADA)]
    dias = ocupacao_por_dia(reservas, quartos, date(2026, 10, 20), date(2026, 10, 22))
    assert [p for _, p in dias] == [50.0, 50.0, 0.0]
    resumo = resumo_periodo(reservas, quartos, date(2026, 10, 20), date(2026, 10, 22))
    assert resumo["reservas"] == 1
    assert resumo["faturamento"] == 200.0
    assert resumo["ticket_medio"] == 200.0
