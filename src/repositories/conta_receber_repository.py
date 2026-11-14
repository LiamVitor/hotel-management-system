from datetime import date

from database.conexao import consultar_todos
from src.models.conta_receber import ContaReceber
from src.utils.constantes import PAGAMENTO_REEMBOLSO, RESERVA_CANCELADA, RESERVA_NO_SHOW

# Vencimento efetivo: a data gravada ou, se faltar, a data de entrada.
_VENCIMENTO = "COALESCE(r.data_vencimento, r.data_entrada)"


class ContaReceberRepository:
    """Consulta das reservas com o que já foi pago. Só lê: as regras ficam no service."""

    def listar(self, vencimento_de=None, vencimento_ate=None):
        """Reservas que podem ter conta a receber (sem canceladas nem no-shows).

        O valor pago já vem somado no banco (pagamentos menos reembolsos), numa consulta só,
        e o filtro por vencimento também é feito lá. Ordem: vencimento mais antigo primeiro.
        """
        sql = f"""
            SELECT r.id AS reserva_id, r.hospede_id, h.nome AS hospede, h.cpf AS cpf,
                   q.numero AS quarto, r.data_entrada, r.data_saida,
                   r.situacao AS situacao_reserva, r.valor_total,
                   {_VENCIMENTO} AS data_vencimento, COALESCE(p.pago, 0) AS pago
            FROM reservas r
            JOIN hospedes h ON h.id = r.hospede_id
            JOIN quartos q ON q.id = r.quarto_id
            LEFT JOIN (SELECT reserva_id,
                              SUM(CASE WHEN tipo = ? THEN -valor ELSE valor END) AS pago
                       FROM pagamentos GROUP BY reserva_id) p ON p.reserva_id = r.id
            WHERE r.situacao NOT IN (?, ?)"""
        parametros = [PAGAMENTO_REEMBOLSO, RESERVA_CANCELADA, RESERVA_NO_SHOW]
        if vencimento_de is not None:
            sql += f" AND {_VENCIMENTO} >= ?"
            parametros.append(vencimento_de.isoformat())
        if vencimento_ate is not None:
            sql += f" AND {_VENCIMENTO} <= ?"
            parametros.append(vencimento_ate.isoformat())
        sql += f" ORDER BY {_VENCIMENTO}, r.id"
        return [ContaReceber(
            reserva_id=l["reserva_id"], hospede_id=l["hospede_id"], hospede=l["hospede"],
            cpf=l["cpf"], quarto=l["quarto"],
            data_entrada=date.fromisoformat(l["data_entrada"]),
            data_saida=date.fromisoformat(l["data_saida"]),
            situacao_reserva=l["situacao_reserva"], valor_total=l["valor_total"],
            valor_pago=round(l["pago"], 2),
            data_vencimento=date.fromisoformat(l["data_vencimento"]),
        ) for l in consultar_todos(sql, tuple(parametros))]
