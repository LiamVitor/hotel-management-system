from datetime import date

import pytest
from database import conexao
from src.models.quarto import Quarto, DISPONIVEL, OCUPADO, MANUTENCAO
from src.repositories.quarto_repository import QuartoRepository


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setattr(conexao, "CAMINHO_BANCO", tmp_path / "teste.db")
    conexao.inicializar_banco()
    return QuartoRepository()


def novo_quarto(numero="101", capacidade=2, preco=150.0, situacao=DISPONIVEL):
    return Quarto(numero=numero, tipo="casal", capacidade=capacidade,
                  preco_diaria=preco, situacao=situacao)


def reservar(quarto_id, entrada, saida, situacao="Hospedada"):
    """Cria hóspede e reserva direto pelo banco, só para montar o cenário."""
    hospede_id = conexao.inserir(
        "INSERT INTO hospedes (nome, cpf) VALUES (?, ?)",
        ("Ana", f"cpf-{quarto_id}-{entrada}"),
    )
    return conexao.inserir(
        """INSERT INTO reservas (hospede_id, quarto_id, data_entrada, data_saida,
                                 valor_diaria, valor_total, situacao)
           VALUES (?, ?, ?, ?, 150, 300, ?)""",
        (hospede_id, quarto_id, entrada.isoformat(), saida.isoformat(), situacao),
    )


def test_criar_e_buscar_por_id(repo):
    criado = repo.criar(novo_quarto())
    assert criado.id is not None
    encontrado = repo.buscar_por_id(criado.id)
    assert encontrado.numero == "101"
    assert encontrado.situacao == DISPONIVEL


def test_buscar_inexistente_retorna_none(repo):
    assert repo.buscar_por_id(999) is None
    assert repo.buscar_por_numero("999") is None


def test_buscar_por_numero(repo):
    repo.criar(novo_quarto("202"))
    assert repo.buscar_por_numero("202").numero == "202"


def test_listar_ordenado_por_numero(repo):
    repo.criar(novo_quarto("102"))
    repo.criar(novo_quarto("101"))
    assert [q.numero for q in repo.listar()] == ["101", "102"]


def test_listar_por_situacao(repo):
    repo.criar(novo_quarto("101"))
    repo.criar(novo_quarto("102", situacao=MANUTENCAO))
    assert [q.numero for q in repo.listar_por_situacao(MANUTENCAO)] == ["102"]


def test_atualizar(repo):
    q = repo.criar(novo_quarto())
    q.preco_diaria = 200.0
    assert repo.atualizar(q) is True
    assert repo.buscar_por_id(q.id).preco_diaria == 200.0


def test_atualizar_situacao(repo):
    q = repo.criar(novo_quarto())
    assert repo.atualizar_situacao(q.id, OCUPADO) is True
    assert repo.buscar_por_id(q.id).situacao == OCUPADO
    assert repo.atualizar_situacao(999, OCUPADO) is False


def test_remover(repo):
    q = repo.criar(novo_quarto())
    assert repo.remover(q.id) is True
    assert repo.buscar_por_id(q.id) is None


def test_numero_duplicado_gera_erro(repo):
    repo.criar(novo_quarto("101"))
    with pytest.raises(Exception):
        repo.criar(novo_quarto("101"))


def test_situacao_invalida_gera_erro(repo):
    with pytest.raises(Exception):
        repo.criar(novo_quarto(situacao="quebrado"))


def test_remover_quarto_com_reserva_gera_erro(repo):
    q = repo.criar(novo_quarto())
    reservar(q.id, date(2026, 10, 20), date(2026, 10, 22))
    with pytest.raises(Exception):
        repo.remover(q.id)


def test_disponiveis_exclui_quarto_com_reserva_no_periodo(repo):
    ocupado = repo.criar(novo_quarto("101"))
    livre = repo.criar(novo_quarto("102"))
    reservar(ocupado.id, date(2026, 10, 20), date(2026, 10, 25))
    numeros = [q.numero for q in repo.listar_disponiveis(date(2026, 10, 22), date(2026, 10, 24))]
    assert numeros == [livre.numero]


def test_disponiveis_dia_de_troca_libera_o_quarto(repo):
    q = repo.criar(novo_quarto("101"))
    reservar(q.id, date(2026, 10, 20), date(2026, 10, 25))
    assert len(repo.listar_disponiveis(date(2026, 10, 25), date(2026, 10, 27))) == 1


def test_disponiveis_ignora_reserva_cancelada(repo):
    q = repo.criar(novo_quarto("101"))
    reservar(q.id, date(2026, 10, 20), date(2026, 10, 25), situacao="Cancelada")
    assert len(repo.listar_disponiveis(date(2026, 10, 21), date(2026, 10, 23))) == 1


def test_disponiveis_exclui_manutencao(repo):
    repo.criar(novo_quarto("101", situacao=MANUTENCAO))
    assert repo.listar_disponiveis(date(2026, 10, 21), date(2026, 10, 23)) == []


def test_disponiveis_respeita_capacidade(repo):
    repo.criar(novo_quarto("101", capacidade=2))
    repo.criar(novo_quarto("102", capacidade=4))
    numeros = [q.numero for q in repo.listar_disponiveis(
        date(2026, 10, 21), date(2026, 10, 23), capacidade_minima=3)]
    assert numeros == ["102"]