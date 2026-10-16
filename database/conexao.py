import sqlite3
from contextlib import contextmanager
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_BANCO = RAIZ / "data" / "hotel.db"
CAMINHO_SCHEMA = RAIZ / "database" / "schema.sql"

def conectar():
    """Abre uma conexão com o banco configurada para o projeto."""
    CAMINHO_BANCO.parent.mkdir(exist_ok=True)
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao

@contextmanager
def obter_conexao():
    """Entrega a conexão, salva (commit) se deu certo e fecha no final."""
    conexao = conectar()
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()

def inicializar_banco():
    """Cria as tabelas a partir do schema.sql (só cria o que ainda não existe)."""
    with obter_conexao() as conexao:
        conexao.executescript(CAMINHO_SCHEMA.read_text(encoding="utf-8"))

def executar(sql, parametros=(), conexao=None):
    """UPDATE / DELETE. Retorna quantas linhas foram afetadas."""
    if conexao is not None:
        return conexao.execute(sql, parametros).rowcount
    with obter_conexao() as nova:
        return nova.execute(sql, parametros).rowcount

def inserir(sql, parametros=(), conexao=None):
    """INSERT. Retorna o id do registro criado."""
    if conexao is not None:
        return conexao.execute(sql, parametros).lastrowid
    with obter_conexao() as nova:
        return nova.execute(sql, parametros).lastrowid

def consultar_um(sql, parametros=(), conexao=None):
    """SELECT de uma linha. Retorna a linha ou None."""
    if conexao is not None:
        return conexao.execute(sql, parametros).fetchone()
    with obter_conexao() as nova:
        return nova.execute(sql, parametros).fetchone()

def consultar_todos(sql, parametros=(), conexao=None):
    """SELECT de várias linhas. Retorna uma lista (vazia se não achar nada)."""
    if conexao is not None:
        return conexao.execute(sql, parametros).fetchall()
    with obter_conexao() as nova:
        return nova.execute(sql, parametros).fetchall()