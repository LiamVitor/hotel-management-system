"""Regras da tela inicial (funções puras, sem banco e sem interface)."""
from src.models.inicio import Alerta, IndicadoresInicio
from src.utils.constantes import (ALERTA_CAIXA_SEM_SALDO, ALERTA_CHECKIN_ATRASADO,
                                  ALERTA_CHECKOUT_ATRASADO, ALERTA_CONTAS_VENCIDAS,
                                  ALERTA_QUARTOS_INDISPONIVEIS, NIVEL_AVISO, NIVEL_CRITICO,
                                  NIVEL_INFO, QUARTO_DISPONIVEL, QUARTO_MANUTENCAO,
                                  QUARTO_OCUPADO, QUARTO_RESERVADO, RESERVA_CONFIRMADA,
                                  RESERVA_FINALIZADA, RESERVA_HOSPEDADA, SITUACOES_QUARTO)
from src.utils.formatacao import formatar_moeda

# Na lista do dia: o que ainda falta fazer vem antes do que já foi feito.
_ORDEM_NA_LISTA = {RESERVA_CONFIRMADA: 0, RESERVA_HOSPEDADA: 1, RESERVA_FINALIZADA: 2}


def saudacao(agora):
    """'Bom dia', 'Boa tarde' ou 'Boa noite' conforme a hora de `agora` (datetime)."""
    if agora.hour < 12:
        return "Bom dia"
    return "Boa tarde" if agora.hour < 18 else "Boa noite"


def contar_situacoes(quartos):
    """{situação: quantidade} de todas as situações de quarto (as sem quarto aparecem com 0)."""
    contagem = {situacao: 0 for situacao in SITUACOES_QUARTO}
    for q in quartos:
        contagem[q.situacao] = contagem.get(q.situacao, 0) + 1
    return contagem


def indicadores(quartos, reservas, hoje):
    """Números dos cartões do dia.

    Quartos: pela situação gravada em cada quarto (a mesma da tela Quartos). A taxa de
    ocupação não conta quartos em manutenção. Chegadas e saídas: pelas datas PREVISTAS;
    "feitas" são as que já passaram pelo check-in / check-out.
    """
    contagem = contar_situacoes(quartos)
    operacionais = len(quartos) - contagem[QUARTO_MANUTENCAO]
    ocupados = contagem[QUARTO_OCUPADO]
    chegadas = [r for r in reservas if r.data_entrada == hoje and r.situacao in _ORDEM_NA_LISTA]
    saidas = [r for r in reservas if r.data_saida == hoje
              and r.situacao in (RESERVA_HOSPEDADA, RESERVA_FINALIZADA)]
    return IndicadoresInicio(
        total_quartos=len(quartos),
        livres=contagem[QUARTO_DISPONIVEL],
        ocupados=ocupados,
        reservados=contagem[QUARTO_RESERVADO],
        em_manutencao=contagem[QUARTO_MANUTENCAO],
        taxa_ocupacao=ocupados / operacionais * 100 if operacionais else 0.0,
        chegadas_previstas=len(chegadas),
        chegadas_feitas=sum(1 for r in chegadas if r.situacao != RESERVA_CONFIRMADA),
        saidas_previstas=len(saidas),
        saidas_feitas=sum(1 for r in saidas if r.situacao == RESERVA_FINALIZADA),
    )


def reservas_do_dia(reservas, hoje):
    """Reservas que movimentam o dia, com o que falta fazer primeiro.

    Confirmadas e hospedadas que cobrem hoje (entrada <= hoje <= saída) e as que saíram hoje.
    Canceladas e no-shows ficam de fora.
    """
    do_dia = [r for r in reservas
              if (r.situacao in (RESERVA_CONFIRMADA, RESERVA_HOSPEDADA)
                  and r.data_entrada <= hoje <= r.data_saida)
              or (r.situacao == RESERVA_FINALIZADA and r.data_saida == hoje)]
    return sorted(do_dia, key=lambda r: (_ORDEM_NA_LISTA[r.situacao], r.data_saida, r.id or 0))


def _quantidade(n, singular, plural):
    return f"{n} {singular if n == 1 else plural}"


def texto_movimento(previstas, feitas):
    """Linha de detalhe dos cartões de check-in / check-out: o que ainda falta fazer."""
    if previstas == 0:
        return "Nenhum previsto"
    pendentes = previstas - feitas
    if pendentes == 0:
        return "Todos realizados"
    return _quantidade(pendentes, "pendente", "pendentes")


def texto_quartos(ind):
    """Linha de detalhe do cartão de quartos disponíveis (reservados e em manutenção)."""
    return (f"{_quantidade(ind.reservados, 'reservado', 'reservados')} · "
            f"{ind.em_manutencao} manutenção")


def alertas(reservas, quartos, quartos_bloqueados, hoje, totais_contas=None,
            caixa_sem_saldo=False):
    """Pendências do dia, das mais urgentes para as informativas.

    quartos_bloqueados: ids dos quartos com bloqueio em andamento agora.
    totais_contas: totais de contas a receber (None se a pessoa não pode ver relatórios).
    caixa_sem_saldo: True se o caixa nunca recebeu um saldo inicial.
    """
    lista = []
    sem_checkin = sum(1 for r in reservas
                      if r.situacao == RESERVA_CONFIRMADA and r.data_entrada < hoje)
    if sem_checkin:
        lista.append(Alerta(
            ALERTA_CHECKIN_ATRASADO, NIVEL_CRITICO,
            f"{_quantidade(sem_checkin, 'reserva com entrada vencida', 'reservas com entrada vencida')}"
            " e sem check-in. Faça o check-in ou marque como não compareceu."))
    sem_checkout = sum(1 for r in reservas
                       if r.situacao == RESERVA_HOSPEDADA and r.data_saida < hoje)
    if sem_checkout:
        lista.append(Alerta(
            ALERTA_CHECKOUT_ATRASADO, NIVEL_CRITICO,
            f"{_quantidade(sem_checkout, 'hospedagem com saída vencida', 'hospedagens com saída vencida')}"
            " e sem check-out."))
    if totais_contas and totais_contas["qtd_vencidas"]:
        n = totais_contas["qtd_vencidas"]
        lista.append(Alerta(
            ALERTA_CONTAS_VENCIDAS, NIVEL_CRITICO,
            f"{_quantidade(n, 'conta vencida', 'contas vencidas')} no total de "
            f"{formatar_moeda(totais_contas['total_vencido'])} a receber."))
    if caixa_sem_saldo:
        lista.append(Alerta(
            ALERTA_CAIXA_SEM_SALDO, NIVEL_AVISO,
            "O saldo inicial do caixa ainda não foi definido: o caixa parte de zero e conta "
            "todo o histórico."))
    indisponiveis = sorted(q.numero for q in quartos
                           if q.situacao == QUARTO_MANUTENCAO or q.id in quartos_bloqueados)
    if indisponiveis:
        rotulo = "Quarto" if len(indisponiveis) == 1 else "Quartos"
        lista.append(Alerta(
            ALERTA_QUARTOS_INDISPONIVEIS, NIVEL_INFO,
            f"{rotulo} {', '.join(indisponiveis)} indisponível hoje (manutenção ou bloqueio)."
            if len(indisponiveis) == 1 else
            f"{rotulo} {', '.join(indisponiveis)} indisponíveis hoje (manutenção ou bloqueio)."))
    return lista
