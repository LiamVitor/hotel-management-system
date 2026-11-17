from datetime import date, datetime, timedelta

from database.conexao import inserir, consultar_um, consultar_todos
from src.models.caixa import Movimentacao, SaldoInicial
from src.utils.constantes import (CAIXA_ENTRADA, CAIXA_SAIDA, ORIGEM_DESPESA, ORIGEM_PAGAMENTO,
                                  ORIGEM_REEMBOLSO)

FORMATO_DATA_HORA = dict(sep=" ", timespec="seconds")

# Cada despesa é uma saída no dia dela (sem hora: vale desde a meia-noite). Excluídas não contam.
_MOVIMENTOS = """
    SELECT p.data_hora AS data_hora,
           p.tipo AS origem, p.id AS origem_id,
           CASE WHEN p.tipo = ? THEN ? ELSE ? END AS tipo,
           p.valor AS valor, p.forma AS detalhe, p.motivo AS texto,
           p.reserva_id AS reserva_id, h.nome AS hospede, u.nome AS responsavel
    FROM pagamentos p
    JOIN reservas r ON r.id = p.reserva_id
    JOIN hospedes h ON h.id = r.hospede_id
    LEFT JOIN usuarios u ON u.id = p.usuario_id
    WHERE p.data_hora >= ? AND p.data_hora < ?
    UNION ALL
    SELECT d.data || ' 00:00:00', ?, d.id, ?, d.valor, c.nome, d.descricao,
           NULL, NULL, u.nome
    FROM despesas d
    JOIN categorias_despesa c ON c.id = d.categoria_id
    LEFT JOIN usuarios u ON u.id = d.usuario_id
    WHERE d.excluida_em IS NULL AND d.data >= ? AND d.data <= ?
"""


def _parametros(inicio, fim):
    """Parâmetros de _MOVIMENTOS para os dias de inicio a fim (inclusive; None = sem limite)."""
    ini_dh = f"{inicio.isoformat()} 00:00:00" if inicio else "0000-01-01 00:00:00"
    fim_dh = f"{(fim + timedelta(days=1)).isoformat()} 00:00:00" if fim else "9999-12-31 23:59:59"
    ini_d = inicio.isoformat() if inicio else "0000-01-01"
    fim_d = fim.isoformat() if fim else "9999-12-31"
    return (ORIGEM_REEMBOLSO, CAIXA_SAIDA, CAIXA_ENTRADA, ini_dh, fim_dh,
            ORIGEM_DESPESA, CAIXA_SAIDA, ini_d, fim_d)


class CaixaRepository:
    """Consultas do caixa e histórico do saldo inicial (que nunca é alterado nem apagado)."""

    # ---------- saldo inicial ----------
    def _saldo_para_objeto(self, linha):
        if linha is None:
            return None
        return SaldoInicial(
            id=linha["id"], valor=linha["valor"],
            data_referencia=date.fromisoformat(linha["data_referencia"]),
            usuario_id=linha["usuario_id"],
            definido_em=datetime.fromisoformat(linha["definido_em"]))

    def definir_saldo_inicial(self, saldo, conexao=None):
        saldo.definido_em = saldo.definido_em or datetime.now().replace(microsecond=0)
        saldo.id = inserir(
            """INSERT INTO caixa_saldo_inicial (valor, data_referencia, usuario_id, definido_em)
               VALUES (?, ?, ?, ?)""",
            (saldo.valor, saldo.data_referencia.isoformat(), saldo.usuario_id,
             saldo.definido_em.isoformat(**FORMATO_DATA_HORA)),
            conexao=conexao)
        return saldo

    def saldo_inicial_vigente(self):
        """A configuração mais recente, ou None se o saldo inicial nunca foi definido."""
        return self._saldo_para_objeto(
            consultar_um("SELECT * FROM caixa_saldo_inicial ORDER BY id DESC LIMIT 1"))

    def historico_saldo_inicial(self):
        """Todas as configurações do saldo inicial, da mais recente para a mais antiga."""
        return [self._saldo_para_objeto(linha) for linha in
                consultar_todos("SELECT * FROM caixa_saldo_inicial ORDER BY id DESC")]

    # ---------- movimentações ----------
    def listar_movimentacoes(self, inicio=None, fim=None):
        """Movimentações dos dias de inicio a fim (inclusive), em ordem cronológica.

        Pagamentos entram (Entrada), reembolsos e despesas saem (Saída). Na mesma hora, as
        entradas vêm antes das saídas.
        """
        linhas = consultar_todos(
            f"SELECT * FROM ({_MOVIMENTOS}) "
            "ORDER BY data_hora, CASE tipo WHEN ? THEN 0 ELSE 1 END, origem, origem_id",
            _parametros(inicio, fim) + (CAIXA_ENTRADA,))
        return [Movimentacao(
            data_hora=datetime.fromisoformat(l["data_hora"]), tipo=l["tipo"], origem=l["origem"],
            origem_id=l["origem_id"], valor=l["valor"], responsavel=l["responsavel"],
            reserva_id=l["reserva_id"],
            descricao=_descrever(l)) for l in linhas]

    def somar_por_origem(self, inicio=None, fim=None):
        """{origem: total} dos dias de inicio a fim (inclusive), feito no banco (sem listar)."""
        linhas = consultar_todos(
            f"SELECT origem, SUM(valor) AS total FROM ({_MOVIMENTOS}) GROUP BY origem",
            _parametros(inicio, fim))
        totais = {ORIGEM_PAGAMENTO: 0.0, ORIGEM_REEMBOLSO: 0.0, ORIGEM_DESPESA: 0.0}
        for l in linhas:
            totais[l["origem"]] = round(l["total"], 2)
        return totais


def _descrever(l):
    """Texto da movimentação para o extrato."""
    if l["origem"] == ORIGEM_DESPESA:
        return f"{l['texto']} ({l['detalhe']})"
    texto = f"{l['origem']} da reserva {l['reserva_id']:04d} — {l['hospede']} ({l['detalhe']})"
    if l["origem"] == ORIGEM_REEMBOLSO and l["texto"]:
        texto += f": {l['texto']}"
    return texto
