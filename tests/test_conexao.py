import pytest
from database import conexao


@pytest.fixture
def banco(tmp_path, monkeypatch):
    monkeypatch.setattr(conexao, "CAMINHO_BANCO", tmp_path / "teste.db")
    conexao.inicializar_banco()


def test_tabelas_sao_criadas(banco):
    linhas = conexao.consultar_todos("SELECT name FROM sqlite_master WHERE type = 'table'")
    nomes = {linha["name"] for linha in linhas}
    assert {"hospedes", "quartos", "reservas"} <= nomes


def test_inserir_e_consultar(banco):
    novo_id = conexao.inserir("INSERT INTO hospedes (nome, cpf) VALUES (?, ?)", ("Ana", "111"))
    hospede = conexao.consultar_um("SELECT * FROM hospedes WHERE id = ?", (novo_id,))
    assert hospede["nome"] == "Ana"


def test_transacao_desfaz_tudo_em_caso_de_erro(banco):
    with pytest.raises(Exception):
        with conexao.obter_conexao() as c:
            conexao.inserir("INSERT INTO hospedes (nome, cpf) VALUES (?, ?)", ("Ana", "111"), conexao=c)
            conexao.inserir("INSERT INTO hospedes (nome, cpf) VALUES (?, ?)", ("Bia", "111"), conexao=c)
    assert conexao.consultar_todos("SELECT * FROM hospedes") == []


def test_chave_estrangeira_e_respeitada(banco):
    with pytest.raises(Exception):
        conexao.inserir(
            "INSERT INTO reservas (hospede_id, quarto_id, data_entrada, data_saida, valor_diaria, valor_total) "
            "VALUES (999, 999, '2026-01-01', '2026-01-02', 100, 100)"
        )