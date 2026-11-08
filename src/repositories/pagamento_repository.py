from datetime import datetime

from database.conexao import inserir, consultar_um, consultar_todos
from src.models.pagamento import Pagamento


class PagamentoRepository:
    """Acesso à tabela pagamentos.

    De propósito não existem atualizar() nem excluir(): um lançamento nunca é alterado
    nem apagado, para o histórico financeiro permanecer íntegro.
    """

    def _para_objeto(self, linha):
        if linha is None:
            return None
        return Pagamento(
            id=linha["id"],
            reserva_id=linha["reserva_id"],
            valor=linha["valor"],
            forma=linha["forma"],
            tipo=linha["tipo"],
            usuario_id=linha["usuario_id"],
            data_hora=datetime.fromisoformat(linha["data_hora"]),
        )

    def _para_objetos(self, linhas):
        return [self._para_objeto(linha) for linha in linhas]

    def criar(self, pagamento, conexao=None):
        pagamento.id = inserir(
            """INSERT INTO pagamentos (reserva_id, data_hora, valor, forma, tipo, usuario_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                pagamento.reserva_id,
                pagamento.data_hora.isoformat(sep=" ", timespec="seconds"),
                pagamento.valor,
                pagamento.forma,
                pagamento.tipo,
                pagamento.usuario_id,
            ),
            conexao=conexao,
        )
        return pagamento

    def buscar_por_id(self, pagamento_id):
        linha = consultar_um("SELECT * FROM pagamentos WHERE id = ?", (pagamento_id,))
        return self._para_objeto(linha)

    def listar_por_reserva(self, reserva_id):
        """Pagamentos da reserva, do mais antigo para o mais recente."""
        linhas = consultar_todos(
            "SELECT * FROM pagamentos WHERE reserva_id = ? ORDER BY data_hora, id",
            (reserva_id,),
        )
        return self._para_objetos(linhas)

    def listar(self):
        linhas = consultar_todos("SELECT * FROM pagamentos ORDER BY data_hora, id")
        return self._para_objetos(linhas)

    def totais_por_reserva(self):
        """{reserva_id: total pago} já descontando reembolsos (uma consulta só)."""
        linhas = consultar_todos(
            """SELECT reserva_id,
                      SUM(CASE WHEN tipo = 'Reembolso' THEN -valor ELSE valor END) AS total
               FROM pagamentos GROUP BY reserva_id"""
        )
        return {linha["reserva_id"]: round(linha["total"], 2) for linha in linhas}
