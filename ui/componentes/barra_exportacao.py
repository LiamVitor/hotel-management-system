"""Botões "Exportar PDF" e "Exportar Excel" de um relatório."""
import os
import subprocess
import sys
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.services.exportacao_regras import EXTENSAO, NOME_DO_FORMATO
from src.utils.constantes import FORMATO_EXCEL, FORMATO_PDF
from ui.componentes.botoes import botao_secundario

TIPOS_DE_ARQUIVO = {FORMATO_PDF: [("Documento PDF", "*.pdf")],
                    FORMATO_EXCEL: [("Planilha do Excel", "*.xlsx")]}


def abrir_arquivo(caminho):
    """Abre o arquivo no programa padrão do sistema (se não der, não faz mal: já foi salvo)."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(caminho)                                   # noqa: S606 (só Windows)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(caminho)])
        else:
            subprocess.Popen(["xdg-open", str(caminho)])
    except (OSError, AttributeError):
        pass


class BarraExportacao(ctk.CTkFrame):
    """Dois botões que salvam o relatório que está na tela em PDF ou Excel.

    chave_relatorio: qual dos oito relatórios é (constantes REL_* de utils/constantes.py).
    obter_documento: função sem argumentos que devolve o `RelatorioPadrao` do que a tela mostra
                     agora (ou levanta ErroNegocio, ex.: 'Escolha um hóspede').
    Quem não tem permissão para exportar o relatório nem vê os botões; mesmo assim o service
    confere de novo (a tela nunca é a única barreira).
    """

    def __init__(self, master, servicos, chave_relatorio, obter_documento):
        super().__init__(master, fg_color="transparent")
        self.servicos = servicos
        self.chave = chave_relatorio
        self._obter_documento = obter_documento
        self.pode = servicos.exportacao.pode_exportar(chave_relatorio)
        if not self.pode:
            return
        botao_secundario(self, "Exportar Excel", lambda: self.exportar(FORMATO_EXCEL), 140
                         ).pack(side="right")
        botao_secundario(self, "Exportar PDF", lambda: self.exportar(FORMATO_PDF), 130
                         ).pack(side="right", padx=(0, 8))

    def exportar(self, formato):
        nome = NOME_DO_FORMATO[formato]
        try:
            documento = self._obter_documento()
            sugerido = self.servicos.exportacao.nome_sugerido(documento, formato)
        except ErroNegocio as erro:
            messagebox.showwarning(f"Exportar {nome}", str(erro))
            return
        destino = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(), title=f"Salvar relatório em {nome}",
            initialfile=sugerido, defaultextension=EXTENSAO[formato],
            filetypes=TIPOS_DE_ARQUIVO[formato])
        if not destino:                                             # a pessoa cancelou
            return
        try:
            caminho = self.servicos.exportacao.exportar(self.chave, documento, formato, destino)
        except ErroNegocio as erro:
            messagebox.showwarning(f"Exportar {nome}", str(erro))
            return
        if messagebox.askyesno(f"Exportar {nome}",
                               f"Relatório salvo em:\n{caminho}\n\nDeseja abrir o arquivo agora?"):
            abrir_arquivo(caminho)
