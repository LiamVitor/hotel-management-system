import math
from datetime import date, datetime

from src.models.caixa import SaldoInicial
from src.repositories.caixa_repository import CaixaRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.services import caixa_regras as regras
from src.services.erros import ErroNegocio
from src.services.relatorios import validar_periodo
from src.utils.constantes import CAIXA_ENTRADA, CAIXA_SAIDA, CAIXA_TODAS
from src.utils.sessao import Sessao

VALOR_MAXIMO = 1_000_000_000


class CaixaService:
    """Controle de caixa: saldo inicial, extrato de movimentações e saldo por período.

    Entradas = pagamentos; saídas = reembolsos e despesas (não excluídas). O extrato é sempre
    calculado a partir desses lançamentos, então nunca fica diferente do que está registrado
    nas reservas e nas despesas.
    """

    def __init__(self, repo=None, usuario_repo=None):
        self.repo = repo or CaixaRepository()
        self.usuario_repo = usuario_repo or UsuarioRepository()

    # ---------- saldo inicial ----------
    def saldo_inicial(self):
        """Configuração vigente do saldo inicial, ou None se ainda não foi definida."""
        Sessao.exigir("caixa.ver")
        return self.repo.saldo_inicial_vigente()

    def definir_saldo_inicial(self, valor, data_referencia):
        """Define (ou troca) o saldo inicial: o que o caixa tinha no começo de data_referencia.

        Cada definição fica no histórico, com quem fez e quando; a mais recente vale. Só o
        movimento a partir da data de referência entra no caixa.
        """
        Sessao.exigir("caixa.configurar")
        if (not isinstance(valor, (int, float)) or isinstance(valor, bool)
                or not math.isfinite(valor)):
            raise ErroNegocio("Informe o valor do saldo inicial.")
        if valor < 0:
            raise ErroNegocio("O saldo inicial não pode ser negativo.")
        if valor > VALOR_MAXIMO:
            raise ErroNegocio("O saldo inicial informado é alto demais.")
        if not isinstance(data_referencia, date) or isinstance(data_referencia, datetime):
            raise ErroNegocio("Informe a data a partir da qual o caixa vale.")
        if data_referencia > date.today():
            raise ErroNegocio("A data do saldo inicial não pode ser futura.")
        return self.repo.definir_saldo_inicial(
            SaldoInicial(valor=round(valor, 2), data_referencia=data_referencia,
                         usuario_id=Sessao.usuario.id))

    def historico_saldo_inicial(self):
        """[(SaldoInicial, nome de quem definiu)], da definição mais recente para a mais antiga."""
        Sessao.exigir("caixa.ver")
        nomes = {}
        resultado = []
        for saldo in self.repo.historico_saldo_inicial():
            if saldo.usuario_id not in nomes:
                usuario = self.usuario_repo.buscar_por_id(saldo.usuario_id)
                nomes[saldo.usuario_id] = usuario.nome if usuario else "—"
            resultado.append((saldo, nomes[saldo.usuario_id]))
        return resultado

    # ---------- período ----------
    def _preparar(self, inicio, fim):
        """Valida o período e devolve (saldo vigente, primeiro dia que vale no caixa)."""
        Sessao.exigir("caixa.ver")
        validar_periodo(inicio, fim)
        vigente = self.repo.saldo_inicial_vigente()
        referencia = vigente.data_referencia if vigente else None
        return vigente, referencia

    def resumo(self, inicio, fim):
        """Saldo no começo do período, entradas, saídas e saldo final (ResumoCaixa)."""
        vigente, referencia = self._preparar(inicio, fim)
        if referencia is not None and fim < referencia:
            return regras.montar_resumo(inicio, fim, None, referencia, {}, {})
        primeiro = max(inicio, referencia) if referencia else inicio
        if referencia is None:
            antes = self.repo.somar_por_origem(None, regras.dia_anterior(inicio))
        elif primeiro > referencia:
            antes = self.repo.somar_por_origem(referencia, regras.dia_anterior(primeiro))
        else:
            antes = {}
        no_periodo = self.repo.somar_por_origem(primeiro, fim)
        return regras.montar_resumo(inicio, fim, vigente.valor if vigente else None,
                                    referencia, antes, no_periodo)

    def movimentacoes(self, inicio, fim, tipo=CAIXA_TODAS):
        """Extrato do período, em ordem cronológica, cada linha com o saldo depois dela.

        tipo: "Todas", "Entrada" ou "Saída". O saldo mostrado é sempre o do caixa inteiro,
        mesmo quando o extrato é filtrado.
        """
        vigente, referencia = self._preparar(inicio, fim)
        if tipo not in (CAIXA_TODAS, CAIXA_ENTRADA, CAIXA_SAIDA):
            raise ErroNegocio("Tipo de movimentação inválido.")
        resumo = self.resumo(inicio, fim)
        if resumo.antes_do_caixa:
            return []
        primeiro = max(inicio, referencia) if referencia else inicio
        movimentos = regras.saldo_acumulado(
            self.repo.listar_movimentacoes(primeiro, fim), resumo.saldo_inicial)
        if tipo != CAIXA_TODAS:
            movimentos = [m for m in movimentos if m.tipo == tipo]
        return movimentos
