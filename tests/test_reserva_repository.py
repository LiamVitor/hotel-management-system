from datetime import date

import pytest
from database import conexao
from src.models.reserva import Reserva
from src.repositories.reserva_repository import ReservaRepository


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setattr(conexao, "CAMINHO_BANCO", tmp_path / "teste.db")
    conexao.inicializar_banco()
    hospede_id = conexao.inserir(
        "INSERT INTO hospedes (nome, cpf) VALUES (?, ?)", ("Ana", "111")
    )
    quarto_id = conexao.inserir(
        "INSERT INTO quartos (numero, tipo, capacidade, preco_diaria) VALUES (?, ?, ?, ?)",
        ("101", "casal", 2, 150.0),
    )
    return ReservaRepository(), hospede_id, quarto_id


def nova_reserva(hospede_id, quarto_id, entrada, saida):
    return Reserva(
        hospede_id=hospede_id,
        quarto_id=quarto_id,
        data_entrada=entrada,
        data_saida=saida,
        valor_diaria=150.0,
        valor_total=300.0,
    )


def test_criar_e_buscar_por_id(ctx):
    repo, hospede_id, quarto_id = ctx
    criada = repo.criar(nova_reserva(hospede_id, quarto_id, date(2026, 10, 20), date(2026, 10, 22)))
    assert criada.id is not None
    encontrada = repo.buscar_por_id(criada.id)
    assert encontrada.data_entrada == date(2026, 10, 20)
    assert encontrada.situacao == "ativa"


def test_buscar_inexistente_retorna_none(ctx):
    repo, _, _ = ctx
    assert repo.buscar_por_id(999) is None


def test_listar_por_hospede_e_por_quarto(ctx):
    repo, hospede_id, quarto_id = ctx
    repo.criar(nova_reserva(hospede_id, quarto_id, date(2026, 10, 20), date(2026, 10, 22)))
    assert len(repo.listar()) == 1
    assert len(repo.listar_por_hospede(hospede_id)) == 1
    assert len(repo.listar_por_quarto(quarto_id)) == 1
    assert repo.listar_por_hospede(999) == []


def test_atualizar(ctx):
    repo, hospede_id, quarto_id = ctx
    r = repo.criar(nova_reserva(hospede_id, quarto_id, date(2026, 10, 20), date(2026, 10, 22)))
    r.data_saida = date(2026, 10, 23)
    r.valor_total = 450.0
    assert repo.atualizar(r) is True
    assert repo.buscar_por_id(r.id).valor_total == 450.0


def test_cancelar_mantem_o_registro(ctx):
    repo, hospede_id, quarto_id = ctx
    r = repo.criar(nova_reserva(hospede_id, quarto_id, date(2026, 10, 20), date(2026, 10, 22)))
    assert repo.cancelar(r.id) is True
    assert repo.buscar_por_id(r.id).situacao == "cancelada"


def test_cancelar_inexistente_retorna_false(ctx):
    repo, _, _ = ctx
    assert repo.cancelar(999) is False


def test_conflito_detecta_sobreposicao(ctx):
    repo, hospede_id, quarto_id = ctx
    repo.criar(nova_reserva(hospede_id, quarto_id, date(2026, 10, 20), date(2026, 10, 25)))
    conflitos = repo.listar_conflitantes(quarto_id, date(2026, 10, 23), date(2026, 10, 27))
    assert len(conflitos) == 1


def test_dia_de_troca_nao_e_conflito(ctx):
    repo, hospede_id, quarto_id = ctx
    repo.criar(nova_reserva(hospede_id, quarto_id, date(2026, 10, 20), date(2026, 10, 25)))
    assert repo.listar_conflitantes(quarto_id, date(2026, 10, 25), date(2026, 10, 27)) == []


def test_reserva_cancelada_nao_gera_conflito(ctx):
    repo, hospede_id, quarto_id = ctx
    r = repo.criar(nova_reserva(hospede_id, quarto_id, date(2026, 10, 20), date(2026, 10, 25)))
    repo.cancelar(r.id)
    assert repo.listar_conflitantes(quarto_id, date(2026, 10, 21), date(2026, 10, 23)) == []


def test_chave_estrangeira_invalida_gera_erro(ctx):
    repo, _, quarto_id = ctx
    with pytest.raises(Exception):
        repo.criar(nova_reserva(999, quarto_id, date(2026, 10, 20), date(2026, 10, 22)))


def test_saida_antes_da_entrada_gera_erro(ctx):
    repo, hospede_id, quarto_id = ctx
    with pytest.raises(Exception):
        repo.criar(nova_reserva(hospede_id, quarto_id, date(2026, 10, 22), date(2026, 10, 20)))