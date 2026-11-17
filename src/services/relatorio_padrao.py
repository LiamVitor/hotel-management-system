"""Padrão de apresentação dos relatórios: cabeçalho, rodapé, paginação e organização (funções puras).

Toda tela de relatório e toda exportação (PDF, planilha...) monta o seu `RelatorioPadrao` por
aqui, então título, período, data/hora de geração e responsável aparecem sempre do mesmo jeito.
"""
import math
import re
from datetime import datetime

from src.models.relatorio_padrao import (ALINHA_DIREITA, ALINHA_ESQUERDA, BlocoPagina,
                                         CabecalhoRelatorio, ColunaRelatorio, FiltroAplicado,
                                         Indicador, Pagina, RelatorioPadrao, RodapePagina,
                                         TabelaRelatorio)
from src.utils.formatacao import formatar_data
from src.utils.pousada import ARQUIVO_LOGO, NOME_POUSADA
from src.utils.permissoes import rotulo_perfil
from src.utils.sessao import Sessao

ROTULO_PERIODO = "Período"
SEM_PERIODO = "Todo o período"

# Capacidade de uma página, em "linhas" de texto. As exportações podem passar outros valores.
LINHAS_POR_PAGINA = 40
LINHAS_DO_CABECALHO = 8          # cabeçalho padrão, só na primeira página
LINHAS_POR_FILEIRA_INDICADORES = 3
INDICADORES_POR_FILEIRA = 4
LINHAS_DO_TITULO_DA_TABELA = 2   # título + linha de colunas

_PARECE_NUMERO = re.compile(r"^[+\-−]?\s*(R\$\s*)?[\d.,]+\s*%?(\s*\(.*\))?$")


def formatar_periodo(inicio, fim, rotulo=ROTULO_PERIODO):
    """'Período: 01/11/2026 a 15/11/2026'. Sem datas: 'Período: Todo o período'."""
    if inicio is None and fim is None:
        texto = SEM_PERIODO
    elif inicio is None:
        texto = f"até {formatar_data(fim)}"
    elif fim is None:
        texto = f"a partir de {formatar_data(inicio)}"
    elif inicio == fim:
        texto = f"em {formatar_data(inicio)}"
    else:
        texto = f"{formatar_data(inicio)} a {formatar_data(fim)}"
    return f"{rotulo}: {texto}"


def descrever_emissor(usuario=None):
    """'Nome (Perfil)' de quem está logado (ou do usuário informado)."""
    usuario = usuario or Sessao.usuario
    if usuario is None:
        return "—"
    return f"{usuario.nome} ({rotulo_perfil(usuario.perfil)})"


def montar_cabecalho(titulo, inicio=None, fim=None, rotulo_periodo=ROTULO_PERIODO,
                     agora=None, usuario=None):
    """Cabeçalho padrão: pousada, título, período, data/hora de geração e responsável pela emissão."""
    return CabecalhoRelatorio(
        nome_pousada=NOME_POUSADA,
        arquivo_logo=str(ARQUIVO_LOGO) if ARQUIVO_LOGO.is_file() else None,
        titulo=titulo,
        periodo=formatar_periodo(inicio, fim, rotulo_periodo),
        gerado_em=(agora or datetime.now()).replace(microsecond=0),
        emitido_por=descrever_emissor(usuario))


def texto_geracao(cabecalho):
    """'Gerado em 15/11/2026 às 12:07'."""
    return f"Gerado em {cabecalho.gerado_em:%d/%m/%Y} às {cabecalho.gerado_em:%H:%M}"


def texto_emissor(cabecalho):
    return f"Emitido por {cabecalho.emitido_por}"


def alinhamento_da_coluna(linhas, chave):
    """Direita para coluna de números, valores em R$ e percentuais; esquerda para o resto."""
    valores = [str(l.get(chave, "")).strip() for l in linhas]
    valores = [v for v in valores if v and v != "—"]
    if valores and all(_PARECE_NUMERO.match(v) for v in valores):
        return ALINHA_DIREITA
    return ALINHA_ESQUERDA


def montar_tabela(titulo, colunas, linhas):
    """colunas: [(titulo, chave, largura)] como na Tabela da tela; linhas: lista de dicionários."""
    linhas = list(linhas)
    return TabelaRelatorio(
        titulo=titulo, linhas=linhas,
        colunas=[ColunaRelatorio(t, chave, largura, alinhamento_da_coluna(linhas, chave))
                 for t, chave, largura in colunas])


def montar_relatorio(cabecalho, indicadores=(), tabelas=(), observacoes=(), filtros=()):
    """Junta as partes na ordem padrão: cabeçalho, filtros, indicadores, tabelas, observações.

    filtros: [(rótulo, valor)] dos filtros ativos na tela (o período já vai no cabeçalho);
    filtro sem valor é descartado.
    """
    return RelatorioPadrao(
        cabecalho=cabecalho, indicadores=[Indicador(r, v) for r, v in indicadores],
        tabelas=list(tabelas), observacoes=[o for o in observacoes if o],
        filtros=[FiltroAplicado(r, str(v)) for r, v in filtros if str(v or "").strip()])


# ---------- rodapé e numeração de páginas ----------
def rodape(cabecalho, pagina, total):
    """Rodapé padrão: pousada e título, quem emitiu e quando, e 'Página N de M'."""
    return RodapePagina(
        esquerda=f"{cabecalho.nome_pousada} — {cabecalho.titulo}",
        centro=f"{texto_emissor(cabecalho)} em {cabecalho.gerado_em:%d/%m/%Y %H:%M}",
        direita=f"Página {pagina} de {total}")


def _linhas_da_primeira_pagina(relatorio, linhas_por_pagina):
    fileiras = math.ceil(len(relatorio.indicadores) / INDICADORES_POR_FILEIRA)
    usadas = LINHAS_DO_CABECALHO + fileiras * LINHAS_POR_FILEIRA_INDICADORES
    return max(linhas_por_pagina - usadas, 0)


def paginar(relatorio, linhas_por_pagina=LINHAS_POR_PAGINA):
    """Divide o relatório em páginas numeradas, cada uma com o rodapé padrão.

    Só a primeira página leva cabeçalho e indicadores. Uma tabela continua na página seguinte
    (com `continuacao=True`, para repetir o título e as colunas); ela só começa numa página se
    couberem o título, as colunas e ao menos uma linha. Sempre há ao menos uma página.
    """
    paginas = [Pagina(numero=1, total=0, com_cabecalho=True)]
    sobra = _linhas_da_primeira_pagina(relatorio, linhas_por_pagina)
    for tabela in relatorio.tabelas:
        restantes, continuacao = list(tabela.linhas), False
        while True:
            if sobra < LINHAS_DO_TITULO_DA_TABELA + 1:
                paginas.append(Pagina(numero=len(paginas) + 1, total=0, com_cabecalho=False))
                sobra = linhas_por_pagina
            cabem = sobra - LINHAS_DO_TITULO_DA_TABELA
            paginas[-1].blocos.append(BlocoPagina(tabela, restantes[:cabem], continuacao))
            sobra -= LINHAS_DO_TITULO_DA_TABELA + len(restantes[:cabem])
            restantes = restantes[cabem:]
            if not restantes:
                break
            continuacao = True
    total = len(paginas)
    for p in paginas:
        p.total = total
        p.rodape = rodape(relatorio.cabecalho, p.numero, total)
    return paginas
