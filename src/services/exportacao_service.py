import os
from pathlib import Path

from src.services import exportacao_regras as regras
from src.services.erros import ErroNegocio
from src.services.exportacao_excel import gerar_excel
from src.services.exportacao_pdf import gerar_pdf
from src.utils.constantes import FORMATO_EXCEL, FORMATO_PDF
from src.utils.sessao import Sessao

_GERADORES = {FORMATO_PDF: gerar_pdf, FORMATO_EXCEL: gerar_excel}


class ExportacaoService:
    """Exporta qualquer relatório da tela (um `RelatorioPadrao`) para PDF ou Excel.

    Quem pode exportar um relatório é quem pode vê-lo (`PERMISSAO_DO_RELATORIO`). A conferência
    é feita aqui, no service: a tela só esconde os botões de quem não pode.
    """

    def nome_sugerido(self, relatorio, formato):
        """Nome de arquivo para o diálogo 'Salvar como' (título e período do relatório)."""
        self._validar_formato(formato)
        return regras.nome_do_arquivo(relatorio, formato)

    def pode_exportar(self, chave_relatorio):
        """True se o usuário logado pode exportar este relatório (para a tela mostrar os botões)."""
        permissao = regras.PERMISSAO_DO_RELATORIO.get(chave_relatorio)
        return permissao is not None and Sessao.pode(permissao)

    def exportar(self, chave_relatorio, relatorio, formato, destino):
        """Grava o relatório em `destino` no formato pedido e devolve o caminho final (Path).

        chave_relatorio: qual dos oito relatórios é (constantes REL_* em utils/constantes.py).
        O arquivo só aparece no destino se foi gerado por inteiro: antes vai para um temporário.
        """
        permissao = regras.PERMISSAO_DO_RELATORIO.get(chave_relatorio)
        if permissao is None:
            raise ErroNegocio("Relatório desconhecido: não é possível exportar.")
        Sessao.exigir(permissao)
        self._validar_formato(formato)
        if relatorio is None or relatorio.cabecalho is None:
            raise ErroNegocio("Gere o relatório antes de exportar.")

        extensao = regras.EXTENSAO[formato]
        destino = Path(destino)
        if destino.suffix.lower() != extensao:
            destino = destino.with_name(destino.name + extensao)
        temporario = destino.with_name(f".{destino.name}.tmp")
        try:
            _GERADORES[formato](relatorio, temporario)
            os.replace(temporario, destino)
        except PermissionError:
            raise ErroNegocio("Não foi possível salvar o arquivo. Se ele estiver aberto em outro "
                              "programa, feche-o e tente de novo, ou escolha outro nome.")
        except OSError as erro:
            raise ErroNegocio(f"Não foi possível salvar o arquivo ({erro.strerror or erro}).")
        finally:
            if temporario.exists():
                try:
                    temporario.unlink()
                except OSError:
                    pass
        return destino

    @staticmethod
    def _validar_formato(formato):
        if formato not in regras.EXTENSAO:
            raise ErroNegocio("Formato de exportação inválido. Use PDF ou Excel.")
