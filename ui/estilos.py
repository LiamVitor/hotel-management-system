"""Cores, fonte e tema da interface."""
import customtkinter as ctk

COR_MENU = "#1F2937"
COR_MENU_HOVER = "#374151"
COR_FUNDO = "#F3F4F6"
COR_CARTAO = "#FFFFFF"
COR_BORDA = "#E5E7EB"
COR_BORDA_CAMPO = "#D1D5DB"
COR_CABECALHO = "#E5E7EB"
COR_LINHA_ALT = "#F9FAFB"
COR_SELECAO = "#DBEAFE"
COR_TEXTO = "#111827"
COR_TEXTO_SUAVE = "#6B7280"

AZUL = "#2563EB"
AZUL_HOVER = "#1D4ED8"
VERMELHO = "#DC2626"
VERMELHO_HOVER = "#B91C1C"
VERDE = "#16A34A"

# Se a Inter não estiver instalada no Windows, o Tk usa uma fonte padrão.
FONTE_FAMILIA = "Inter"


def configurar_tema():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")


def fonte(tamanho=13, negrito=False):
    return ctk.CTkFont(family=FONTE_FAMILIA, size=tamanho, weight="bold" if negrito else "normal")
