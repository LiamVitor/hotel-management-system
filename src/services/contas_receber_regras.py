"""Regras do relatório de contas a receber (funções puras, sem banco e sem interface)."""
from src.services.pagamento_regras import arredondar, saldo_pendente
from src.utils.constantes import (CONTA_A_VENCER, CONTA_QUITADA, CONTA_VENCIDA, CONTAS_A_VENCER,
                                  CONTAS_EM_ABERTO, CONTAS_QUITADAS, CONTAS_TODAS,
                                  CONTAS_VENCIDAS)
from src.utils.filtros import normalizar_texto, parece_numerico
from src.utils.formatacao import apenas_digitos

# filtro do relatório -> situações que ele mostra
SITUACOES_DO_FILTRO = {
    CONTAS_EM_ABERTO: {CONTA_A_VENCER, CONTA_VENCIDA},
    CONTAS_VENCIDAS: {CONTA_VENCIDA},
    CONTAS_A_VENCER: {CONTA_A_VENCER},
    CONTAS_QUITADAS: {CONTA_QUITADA},
    CONTAS_TODAS: {CONTA_QUITADA, CONTA_A_VENCER, CONTA_VENCIDA},
}


def situacao_financeira(saldo, vencimento, hoje):
    """Quitada (nada a receber), A vencer (vence hoje ou depois) ou Vencida (já passou)."""
    if saldo <= 0:
        return CONTA_QUITADA
    return CONTA_VENCIDA if vencimento < hoje else CONTA_A_VENCER


def dias_em_atraso(saldo, vencimento, hoje):
    """Quantos dias passaram do vencimento (0 se quitada ou ainda no prazo)."""
    if saldo <= 0 or vencimento >= hoje:
        return 0
    return (hoje - vencimento).days


def calcular(conta, hoje):
    """Preenche saldo, situação e dias em atraso de uma ContaReceber e devolve ela."""
    conta.saldo = saldo_pendente(conta.valor_total, conta.valor_pago)
    conta.situacao = situacao_financeira(conta.saldo, conta.data_vencimento, hoje)
    conta.dias_em_atraso = dias_em_atraso(conta.saldo, conta.data_vencimento, hoje)
    return conta


def filtrar(contas, filtro=CONTAS_EM_ABERTO, termo=""):
    """Contas da situação pedida cujo hóspede, CPF, quarto ou código batem com o termo."""
    situacoes = SITUACOES_DO_FILTRO[filtro]
    termo = (termo or "").strip()
    texto = normalizar_texto(termo)
    digitos = apenas_digitos(termo) if parece_numerico(termo) else ""
    resultado = []
    for c in contas:
        if c.situacao not in situacoes:
            continue
        if termo:
            campos = [f"{c.reserva_id:04d}", normalizar_texto(c.hospede),
                      normalizar_texto(c.quarto)]
            achou = any(texto in campo for campo in campos)
            if not achou and digitos:
                achou = digitos in apenas_digitos(c.cpf)
            if not achou:
                continue
        resultado.append(c)
    return resultado


def totalizar(contas):
    """Somas do que está na lista (normalmente já filtrada)."""
    em_aberto = [c for c in contas if c.situacao != CONTA_QUITADA]
    vencidas = [c for c in contas if c.situacao == CONTA_VENCIDA]
    a_vencer = [c for c in contas if c.situacao == CONTA_A_VENCER]
    return {
        "reservas": len(contas),
        "valor_total": arredondar(sum(c.valor_total for c in contas)),
        "valor_pago": arredondar(sum(c.valor_pago for c in contas)),
        "total_a_receber": arredondar(sum(c.saldo for c in em_aberto)),
        "total_vencido": arredondar(sum(c.saldo for c in vencidas)),
        "total_a_vencer": arredondar(sum(c.saldo for c in a_vencer)),
        "qtd_em_aberto": len(em_aberto),
        "qtd_vencidas": len(vencidas),
    }
