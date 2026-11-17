import pytest
from database import conexao
from src.models.hospede import Hospede
from src.repositories.hospede_repository import HospedeRepository


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setattr(conexao, "CAMINHO_BANCO", tmp_path / "teste.db")
    conexao.inicializar_banco()
    return HospedeRepository()


def test_criar_e_buscar_por_id(repo):
    criado = repo.criar(Hospede(nome="Ana", cpf="111"))
    assert criado.id is not None
    assert repo.buscar_por_id(criado.id).nome == "Ana"


def test_buscar_inexistente_retorna_none(repo):
    assert repo.buscar_por_id(999) is None


def test_listar(repo):
    repo.criar(Hospede(nome="Bia", cpf="222"))
    repo.criar(Hospede(nome="Ana", cpf="111"))
    assert [h.nome for h in repo.listar()] == ["Ana", "Bia"]


def test_atualizar(repo):
    h = repo.criar(Hospede(nome="Ana", cpf="111"))
    h.telefone = "86999999999"
    assert repo.atualizar(h) is True
    assert repo.buscar_por_id(h.id).telefone == "86999999999"


def test_remover(repo):
    h = repo.criar(Hospede(nome="Ana", cpf="111"))
    assert repo.remover(h.id) is True
    assert repo.buscar_por_id(h.id) is None


def test_cpf_duplicado_gera_erro(repo):
    repo.criar(Hospede(nome="Ana", cpf="111"))
    with pytest.raises(Exception):
        repo.criar(Hospede(nome="Bia", cpf="111"))