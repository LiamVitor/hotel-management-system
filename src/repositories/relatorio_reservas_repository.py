from datetime import date, datetime, timedelta

from database.conexao import consultar_todos
from src.models.relatorio_reservas import MovimentoHospedagem, ReservaDoPeriodo
from src.utils.constantes import MOVIMENTO_CHECKIN, MOVIMENTO_CHECKOUT, PAGAMENTO_REEMBOLSO


def _data_hora(valor):
    return datetime.fromisoformat(valor) if valor else None


class RelatorioReservasRepository:
    """Consultas dos relatórios de reservas por período e de check-ins/check-outs.

    Só lê. Os filtros de período e de situação são feitos no banco, e o valor pago já vem somado
    (pagamentos menos reembolsos) numa consulta só.
    """

    def reservas_com_entrada_no_periodo(self, inicio, fim, situacao=None):
        """Reservas cuja data de entrada prevista está entre inicio e fim (inclusive), de qualquer
        situação (ou só da pedida), da entrada mais antiga para a mais nova."""
        sql = """
            SELECT r.id AS reserva_id, h.nome AS hospede, h.cpf AS cpf, q.numero AS quarto,
                   q.tipo AS tipo_quarto, r.data_entrada, r.data_saida, r.situacao,
                   r.valor_total, r.criada_em, COALESCE(p.pago, 0) AS pago
            FROM reservas r
            JOIN hospedes h ON h.id = r.hospede_id
            JOIN quartos q ON q.id = r.quarto_id
            LEFT JOIN (SELECT reserva_id,
                              SUM(CASE WHEN tipo = ? THEN -valor ELSE valor END) AS pago
                       FROM pagamentos GROUP BY reserva_id) p ON p.reserva_id = r.id
            WHERE r.data_entrada >= ? AND r.data_entrada <= ?"""
        parametros = [PAGAMENTO_REEMBOLSO, inicio.isoformat(), fim.isoformat()]
        if situacao:
            sql += " AND r.situacao = ?"
            parametros.append(situacao)
        sql += " ORDER BY r.data_entrada, r.id"
        return [ReservaDoPeriodo(
            reserva_id=l["reserva_id"], hospede=l["hospede"], cpf=l["cpf"], quarto=l["quarto"],
            tipo_quarto=l["tipo_quarto"], data_entrada=date.fromisoformat(l["data_entrada"]),
            data_saida=date.fromisoformat(l["data_saida"]), situacao=l["situacao"],
            valor_total=l["valor_total"], valor_pago=round(l["pago"], 2),
            criada_em=_data_hora(l["criada_em"]),
        ) for l in consultar_todos(sql, tuple(parametros))]

    def movimentos_no_periodo(self, inicio, fim, tipo=None):
        """Check-ins e check-outs realizados de inicio a fim (inclusive), em ordem cronológica.

        tipo: só 'Check-in' ou só 'Check-out' (None = os dois). A data/hora é a REAL gravada no
        momento da operação; a prevista vem da reserva.
        """
        de = inicio.isoformat()
        ate = (fim + timedelta(days=1)).isoformat()      # exclusivo: pega o dia final inteiro
        partes, parametros = [], []
        for nome, coluna_quando, coluna_quem, coluna_prevista in (
                (MOVIMENTO_CHECKIN, "checkin_em", "checkin_por", "data_entrada"),
                (MOVIMENTO_CHECKOUT, "checkout_em", "checkout_por", "data_saida")):
            if tipo and tipo != nome:
                continue
            partes.append(f"""
                SELECT r.id AS reserva_id, h.nome AS hospede, h.cpf AS cpf, q.numero AS quarto,
                       '{nome}' AS tipo, r.{coluna_quando} AS quando,
                       r.{coluna_prevista} AS prevista, u.nome AS responsavel
                FROM reservas r
                JOIN hospedes h ON h.id = r.hospede_id
                JOIN quartos q ON q.id = r.quarto_id
                LEFT JOIN usuarios u ON u.id = r.{coluna_quem}
                WHERE r.{coluna_quando} IS NOT NULL
                  AND r.{coluna_quando} >= ? AND r.{coluna_quando} < ?""")
            parametros += [de, ate]
        if not partes:
            return []
        sql = " UNION ALL ".join(partes) + " ORDER BY quando, tipo DESC, reserva_id"
        return [MovimentoHospedagem(
            reserva_id=l["reserva_id"], hospede=l["hospede"], cpf=l["cpf"], quarto=l["quarto"],
            tipo=l["tipo"], data_hora=datetime.fromisoformat(l["quando"]),
            data_prevista=date.fromisoformat(l["prevista"]),
            responsavel=l["responsavel"] or "—",
        ) for l in consultar_todos(sql, tuple(parametros))]
