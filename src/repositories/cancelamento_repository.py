from datetime import date, datetime, timedelta

from database.conexao import consultar_todos
from src.models.registro_cancelamento import RegistroCancelamento
from src.utils.constantes import PAGAMENTO_REEMBOLSO, RESERVA_CANCELADA, RESERVA_NO_SHOW

_EVENTO = "COALESCE(r.cancelada_em, r.noshow_em)"


def _data_hora(valor):
    return datetime.fromisoformat(valor) if valor else None


class CancelamentoRepository:
    """Consulta das reservas canceladas e de no-show com o que foi pago e reembolsado."""

    def listar(self, situacao=None, evento_de=None, evento_ate=None):
        """Reservas canceladas e de no-show, da mais recente para a mais antiga.

        situacao: só Cancelada ou só Não compareceu (None = as duas).
        evento_de / evento_ate: dias (inclusive) em que o cancelamento ou o no-show aconteceu.
        Pagamentos e reembolsos já vêm somados do banco, em uma consulta só.
        """
        situacoes = (situacao,) if situacao else (RESERVA_CANCELADA, RESERVA_NO_SHOW)
        sql = f"""
            SELECT r.id AS reserva_id, r.hospede_id, h.nome AS hospede, h.cpf AS cpf,
                   q.numero AS quarto, r.situacao, r.criada_em, r.data_entrada,
                   {_EVENTO} AS evento_em, r.cancelamento_motivo AS motivo,
                   u.nome AS responsavel, r.valor_total,
                   r.retencao_percentual, r.valor_retido,
                   COALESCE(p.bruto, 0) AS bruto, COALESCE(p.reembolsado, 0) AS reembolsado
            FROM reservas r
            JOIN hospedes h ON h.id = r.hospede_id
            JOIN quartos q ON q.id = r.quarto_id
            LEFT JOIN usuarios u
                   ON u.id = CASE WHEN r.situacao = ? THEN r.cancelada_por ELSE r.noshow_por END
            LEFT JOIN (SELECT reserva_id,
                              SUM(CASE WHEN tipo = ? THEN 0 ELSE valor END) AS bruto,
                              SUM(CASE WHEN tipo = ? THEN valor ELSE 0 END) AS reembolsado
                       FROM pagamentos GROUP BY reserva_id) p ON p.reserva_id = r.id
            WHERE r.situacao IN ({", ".join("?" * len(situacoes))})"""
        parametros = [RESERVA_CANCELADA, PAGAMENTO_REEMBOLSO, PAGAMENTO_REEMBOLSO, *situacoes]
        if evento_de is not None:
            sql += f" AND {_EVENTO} >= ?"
            parametros.append(f"{evento_de.isoformat()} 00:00:00")
        if evento_ate is not None:
            sql += f" AND {_EVENTO} < ?"
            parametros.append(f"{(evento_ate + timedelta(days=1)).isoformat()} 00:00:00")
        sql += f" ORDER BY {_EVENTO} DESC, r.id DESC"
        return [RegistroCancelamento(
            reserva_id=l["reserva_id"], hospede_id=l["hospede_id"], hospede=l["hospede"],
            cpf=l["cpf"], quarto=l["quarto"], situacao=l["situacao"],
            criada_em=_data_hora(l["criada_em"]),
            data_entrada=date.fromisoformat(l["data_entrada"]),
            evento_em=_data_hora(l["evento_em"]), motivo=l["motivo"],
            responsavel=l["responsavel"], valor_total=l["valor_total"],
            pago_bruto=round(l["bruto"], 2), reembolsado=round(l["reembolsado"], 2),
            retencao_percentual=l["retencao_percentual"], valor_retido=l["valor_retido"],
        ) for l in consultar_todos(sql, tuple(parametros))]
