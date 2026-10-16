from datetime import date

from database.conexao import inserir, executar, consultar_um, consultar_todos
from src.models.reserva import Reserva


class ReservaRepository:

    def _para_objeto(self, linha):
        if linha is None:
            return None
        return Reserva(
            id=linha["id"],
            hospede_id=linha["hospede_id"],
            quarto_id=linha["quarto_id"],
            data_entrada=date.fromisoformat(linha["data_entrada"]),
            data_saida=date.fromisoformat(linha["data_saida"]),
            valor_diaria=linha["valor_diaria"],
            valor_total=linha["valor_total"],
            situacao=linha["situacao"],
        )

    def _para_objetos(self, linhas):
        return [self._para_objeto(linha) for linha in linhas]

    def criar(self, reserva, conexao=None):
        reserva.id = inserir(
            """INSERT INTO reservas
               (hospede_id, quarto_id, data_entrada, data_saida,
                valor_diaria, valor_total, situacao)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                reserva.hospede_id,
                reserva.quarto_id,
                reserva.data_entrada.isoformat(),
                reserva.data_saida.isoformat(),
                reserva.valor_diaria,
                reserva.valor_total,
                reserva.situacao,
            ),
            conexao=conexao,
        )
        return reserva

    def buscar_por_id(self, reserva_id):
        linha = consultar_um("SELECT * FROM reservas WHERE id = ?", (reserva_id,))
        return self._para_objeto(linha)

    def listar(self):
        linhas = consultar_todos("SELECT * FROM reservas ORDER BY data_entrada DESC")
        return self._para_objetos(linhas)

    def listar_por_hospede(self, hospede_id):
        linhas = consultar_todos(
            "SELECT * FROM reservas WHERE hospede_id = ? ORDER BY data_entrada DESC",
            (hospede_id,),
        )
        return self._para_objetos(linhas)

    def listar_por_quarto(self, quarto_id):
        linhas = consultar_todos(
            "SELECT * FROM reservas WHERE quarto_id = ? ORDER BY data_entrada DESC",
            (quarto_id,),
        )
        return self._para_objetos(linhas)

    def listar_conflitantes(self, quarto_id, data_entrada, data_saida, ignorar_id=None):
        """Reservas ativas do quarto que se sobrepõem ao período informado.
        Só consulta. Quem decide o que fazer com isso é o service."""
        linhas = consultar_todos(
            """SELECT * FROM reservas
               WHERE quarto_id = ?
                 AND situacao = 'ativa'
                 AND data_entrada < ?
                 AND data_saida > ?
                 AND id != ?""",
            (quarto_id, data_saida.isoformat(), data_entrada.isoformat(), ignorar_id or -1),
        )
        return self._para_objetos(linhas)

    def atualizar(self, reserva, conexao=None):
        afetadas = executar(
            """UPDATE reservas
               SET hospede_id = ?, quarto_id = ?, data_entrada = ?, data_saida = ?,
                   valor_diaria = ?, valor_total = ?, situacao = ?
               WHERE id = ?""",
            (
                reserva.hospede_id,
                reserva.quarto_id,
                reserva.data_entrada.isoformat(),
                reserva.data_saida.isoformat(),
                reserva.valor_diaria,
                reserva.valor_total,
                reserva.situacao,
                reserva.id,
            ),
            conexao=conexao,
        )
        return afetadas > 0

    def cancelar(self, reserva_id, conexao=None):
        afetadas = executar(
            "UPDATE reservas SET situacao = 'cancelada' WHERE id = ?",
            (reserva_id,),
            conexao=conexao,
        )
        return afetadas > 0