from database.conexao import inserir, executar, consultar_um, consultar_todos
from src.models.quarto import Quarto
from src.utils.constantes import QUARTO_MANUTENCAO, RESERVA_CONFIRMADA, RESERVA_HOSPEDADA


class QuartoRepository:

    def _para_objeto(self, linha):
        if linha is None:
            return None
        return Quarto(
            id=linha["id"],
            numero=linha["numero"],
            tipo=linha["tipo"],
            capacidade=linha["capacidade"],
            preco_diaria=linha["preco_diaria"],
            situacao=linha["situacao"],
        )

    def _para_objetos(self, linhas):
        return [self._para_objeto(linha) for linha in linhas]

    def criar(self, quarto, conexao=None):
        quarto.id = inserir(
            """INSERT INTO quartos (numero, tipo, capacidade, preco_diaria, situacao)
               VALUES (?, ?, ?, ?, ?)""",
            (quarto.numero, quarto.tipo, quarto.capacidade,
             quarto.preco_diaria, quarto.situacao),
            conexao=conexao,
        )
        return quarto

    def buscar_por_id(self, quarto_id):
        linha = consultar_um("SELECT * FROM quartos WHERE id = ?", (quarto_id,))
        return self._para_objeto(linha)

    def buscar_por_numero(self, numero):
        linha = consultar_um("SELECT * FROM quartos WHERE numero = ?", (numero,))
        return self._para_objeto(linha)

    def listar(self):
        linhas = consultar_todos("SELECT * FROM quartos ORDER BY numero")
        return self._para_objetos(linhas)

    def listar_por_situacao(self, situacao):
        linhas = consultar_todos(
            "SELECT * FROM quartos WHERE situacao = ? ORDER BY numero",
            (situacao,),
        )
        return self._para_objetos(linhas)

    def listar_disponiveis(self, data_entrada, data_saida, capacidade_minima=1):
        """Quartos que não estão em manutenção, comportam o número de pessoas
        e não têm reserva (confirmada ou hospedada) sobreposta ao período."""
        linhas = consultar_todos(
            """SELECT * FROM quartos
               WHERE situacao != ?
                 AND capacidade >= ?
                 AND id NOT IN (
                     SELECT quarto_id FROM reservas
                     WHERE situacao IN (?, ?)
                       AND data_entrada < ?
                       AND data_saida > ?
                 )
               ORDER BY numero""",
            (QUARTO_MANUTENCAO, capacidade_minima, RESERVA_CONFIRMADA, RESERVA_HOSPEDADA,
             data_saida.isoformat(), data_entrada.isoformat()),
        )
        return self._para_objetos(linhas)

    def atualizar(self, quarto, conexao=None):
        afetadas = executar(
            """UPDATE quartos
               SET numero = ?, tipo = ?, capacidade = ?, preco_diaria = ?, situacao = ?
               WHERE id = ?""",
            (quarto.numero, quarto.tipo, quarto.capacidade,
             quarto.preco_diaria, quarto.situacao, quarto.id),
            conexao=conexao,
        )
        return afetadas > 0

    def atualizar_situacao(self, quarto_id, situacao, conexao=None):
        afetadas = executar(
            "UPDATE quartos SET situacao = ? WHERE id = ?",
            (situacao, quarto_id),
            conexao=conexao,
        )
        return afetadas > 0

    def remover(self, quarto_id):
        afetadas = executar("DELETE FROM quartos WHERE id = ?", (quarto_id,))
        return afetadas > 0
