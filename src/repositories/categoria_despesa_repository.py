from database.conexao import inserir, executar, consultar_um, consultar_todos
from src.models.despesa import CategoriaDespesa


class CategoriaDespesaRepository:
    """Categorias de despesa. Não existe excluir(): categoria só é desativada."""

    def _para_objeto(self, linha):
        if linha is None:
            return None
        return CategoriaDespesa(id=linha["id"], nome=linha["nome"], ativa=bool(linha["ativa"]))

    def criar(self, categoria, conexao=None):
        categoria.id = inserir("INSERT INTO categorias_despesa (nome, ativa) VALUES (?, ?)",
                               (categoria.nome, int(categoria.ativa)), conexao=conexao)
        return categoria

    def atualizar(self, categoria):
        executar("UPDATE categorias_despesa SET nome = ?, ativa = ? WHERE id = ?",
                 (categoria.nome, int(categoria.ativa), categoria.id))

    def buscar_por_id(self, categoria_id):
        return self._para_objeto(consultar_um(
            "SELECT * FROM categorias_despesa WHERE id = ?", (categoria_id,)))

    def listar(self, apenas_ativas=False):
        sql = "SELECT * FROM categorias_despesa"
        if apenas_ativas:
            sql += " WHERE ativa = 1"
        return [self._para_objeto(linha)
                for linha in consultar_todos(sql + " ORDER BY nome COLLATE NOCASE")]
