from datetime import date, datetime

from database.conexao import inserir, executar, consultar_um, consultar_todos
from src.models.despesa import Despesa

FORMATO_DATA_HORA = dict(sep=" ", timespec="seconds")


def _data_hora(valor):
    return datetime.fromisoformat(valor) if valor else None


class DespesaRepository:
    """Acesso à tabela despesas. Excluir é só marcar a linha (excluida_em); nada é apagado."""

    def _para_objeto(self, linha):
        if linha is None:
            return None
        return Despesa(
            id=linha["id"],
            data=date.fromisoformat(linha["data"]),
            descricao=linha["descricao"],
            valor=linha["valor"],
            categoria_id=linha["categoria_id"],
            usuario_id=linha["usuario_id"],
            criada_em=datetime.fromisoformat(linha["criada_em"]),
            atualizada_em=_data_hora(linha["atualizada_em"]),
            atualizada_por=linha["atualizada_por"],
            excluida_em=_data_hora(linha["excluida_em"]),
            excluida_por=linha["excluida_por"],
        )

    def criar(self, despesa, conexao=None):
        despesa.id = inserir(
            """INSERT INTO despesas (data, descricao, valor, categoria_id, usuario_id, criada_em)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (despesa.data.isoformat(), despesa.descricao, despesa.valor, despesa.categoria_id,
             despesa.usuario_id, despesa.criada_em.isoformat(**FORMATO_DATA_HORA)),
            conexao=conexao,
        )
        return despesa

    def atualizar(self, despesa):
        """Grava os novos dados e quem/quando alterou. Devolve False se a despesa já foi excluída."""
        alteradas = executar(
            """UPDATE despesas SET data = ?, descricao = ?, valor = ?, categoria_id = ?,
                      atualizada_em = ?, atualizada_por = ?
               WHERE id = ? AND excluida_em IS NULL""",
            (despesa.data.isoformat(), despesa.descricao, despesa.valor, despesa.categoria_id,
             despesa.atualizada_em.isoformat(**FORMATO_DATA_HORA), despesa.atualizada_por,
             despesa.id))
        return alteradas > 0

    def excluir(self, despesa_id, usuario_id, quando):
        """Marca como excluída (e guarda quem e quando). Devolve False se já estava excluída."""
        alteradas = executar(
            "UPDATE despesas SET excluida_em = ?, excluida_por = ? "
            "WHERE id = ? AND excluida_em IS NULL",
            (quando.isoformat(**FORMATO_DATA_HORA), usuario_id, despesa_id))
        return alteradas > 0

    def buscar_por_id(self, despesa_id, incluir_excluidas=False):
        sql = "SELECT * FROM despesas WHERE id = ?"
        if not incluir_excluidas:
            sql += " AND excluida_em IS NULL"
        return self._para_objeto(consultar_um(sql, (despesa_id,)))

    def listar(self, data_de=None, data_ate=None, categoria_id=None):
        """Despesas não excluídas, da mais recente para a mais antiga (datas inclusivas)."""
        sql = "SELECT * FROM despesas WHERE excluida_em IS NULL"
        parametros = []
        if data_de is not None:
            sql += " AND data >= ?"
            parametros.append(data_de.isoformat())
        if data_ate is not None:
            sql += " AND data <= ?"
            parametros.append(data_ate.isoformat())
        if categoria_id is not None:
            sql += " AND categoria_id = ?"
            parametros.append(categoria_id)
        sql += " ORDER BY data DESC, id DESC"
        return [self._para_objeto(linha) for linha in consultar_todos(sql, tuple(parametros))]

    def contar_por_categoria(self):
        """{categoria_id: quantas despesas (não excluídas) usam a categoria}."""
        linhas = consultar_todos(
            "SELECT categoria_id, COUNT(*) AS total FROM despesas "
            "WHERE excluida_em IS NULL GROUP BY categoria_id")
        return {linha["categoria_id"]: linha["total"] for linha in linhas}
