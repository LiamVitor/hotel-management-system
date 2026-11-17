from database.conexao import inserir, executar, consultar_um, consultar_todos
from src.models.hospede import Hospede


class HospedeRepository:

    def _para_objeto(self, linha):
        """Converte uma linha do banco em um objeto Hospede."""
        if linha is None:
            return None
        return Hospede(
            id=linha["id"],
            nome=linha["nome"],
            cpf=linha["cpf"],
            telefone=linha["telefone"],
            email=linha["email"],
        )

    def criar(self, hospede):
        hospede.id = inserir(
            "INSERT INTO hospedes (nome, cpf, telefone, email) VALUES (?, ?, ?, ?)",
            (hospede.nome, hospede.cpf, hospede.telefone, hospede.email),
        )
        return hospede

    def buscar_por_id(self, hospede_id):
        linha = consultar_um("SELECT * FROM hospedes WHERE id = ?", (hospede_id,))
        return self._para_objeto(linha)

    def buscar_por_cpf(self, cpf):
        linha = consultar_um("SELECT * FROM hospedes WHERE cpf = ?", (cpf,))
        return self._para_objeto(linha)

    def listar(self):
        linhas = consultar_todos("SELECT * FROM hospedes ORDER BY nome")
        return [self._para_objeto(linha) for linha in linhas]

    def atualizar(self, hospede):
        afetadas = executar(
            "UPDATE hospedes SET nome = ?, cpf = ?, telefone = ?, email = ? WHERE id = ?",
            (hospede.nome, hospede.cpf, hospede.telefone, hospede.email, hospede.id),
        )
        return afetadas > 0   # False se o id não existia

    def remover(self, hospede_id):
        afetadas = executar("DELETE FROM hospedes WHERE id = ?", (hospede_id,))
        return afetadas > 0