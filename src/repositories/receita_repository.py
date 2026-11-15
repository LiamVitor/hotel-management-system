from datetime import timedelta

from database.conexao import consultar_todos
from src.utils.constantes import RESERVA_CANCELADA, RESERVA_NO_SHOW

_LIQUIDO_POR_RESERVA = """
    SELECT reserva_id,
           SUM(CASE WHEN tipo = 'Reembolso' THEN -valor ELSE valor END) AS liquido
    FROM pagamentos GROUP BY reserva_id
"""


class ReceitaRepository:
    """Consultas do demonstrativo de receitas; tudo agregado e filtrado no banco."""

    def reservado(self, inicio, fim):
        """Reservas ativas que entram de inicio a fim (inclusive), por dia de entrada e quarto.

        Cada linha: dia, quarto_id, numero, tipo, qtd, reservado (soma do valor total) e
        a_receber (soma do saldo pendente de cada reserva, nunca negativo).
        """
        return [dict(l) for l in consultar_todos(
            f"""SELECT r.data_entrada AS dia, q.id AS quarto_id, q.numero AS numero,
                       q.tipo AS tipo, COUNT(*) AS qtd, SUM(r.valor_total) AS reservado,
                       SUM(MAX(r.valor_total - COALESCE(t.liquido, 0), 0)) AS a_receber
                FROM reservas r
                JOIN quartos q ON q.id = r.quarto_id
                LEFT JOIN ({_LIQUIDO_POR_RESERVA}) t ON t.reserva_id = r.id
                WHERE r.situacao NOT IN (?, ?) AND r.data_entrada >= ? AND r.data_entrada <= ?
                GROUP BY r.data_entrada, q.id""",
            (RESERVA_CANCELADA, RESERVA_NO_SHOW, inicio.isoformat(), fim.isoformat()))]

    def recebimentos(self, inicio, fim):
        """Pagamentos e reembolsos de inicio a fim (inclusive), pela data do lançamento.

        Cada linha: dia, forma, tipo (Pagamento | Reembolso), quarto_id, numero, tipo_quarto,
        total e qtd. Cancelamentos e no-shows entram: o que foi pago (e ficou retido) é receita.
        """
        return [dict(l) for l in consultar_todos(
            """SELECT substr(p.data_hora, 1, 10) AS dia, p.forma AS forma, p.tipo AS tipo,
                      q.id AS quarto_id, q.numero AS numero, q.tipo AS tipo_quarto,
                      SUM(p.valor) AS total, COUNT(*) AS qtd
               FROM pagamentos p
               JOIN reservas r ON r.id = p.reserva_id
               JOIN quartos q ON q.id = r.quarto_id
               WHERE p.data_hora >= ? AND p.data_hora < ?
               GROUP BY dia, p.forma, p.tipo, q.id""",
            (f"{inicio.isoformat()} 00:00:00",
             f"{(fim + timedelta(days=1)).isoformat()} 00:00:00"))]
