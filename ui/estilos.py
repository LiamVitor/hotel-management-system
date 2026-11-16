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
AMARELO = "#F59E0B"
AZUL_CLARO = "#93C5FD"

# Tamanho do número nos cartões de indicadores de todos os relatórios
TAMANHO_INDICADOR = 21

# Se a Inter não estiver instalada no Windows, o Tk usa uma fonte padrão.
FONTE_FAMILIA = "Inter"


def configurar_tema():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")


def fonte(tamanho=13, negrito=False):
    return ctk.CTkFont(family=FONTE_FAMILIA, size=tamanho, weight="bold" if negrito else "normal")


# Paleta semântica para badges de status nas tabelas.
# Pares: (cor de fundo, cor do texto).
BADGE_VERDE = ("#DCFCE7", "#166534")
BADGE_AZUL = ("#DBEAFE", "#1D4ED8")
BADGE_VERMELHO = ("#FEE2E2", "#B91C1C")
BADGE_AMARELO = ("#FEF3C7", "#92400E")
BADGE_ROXO = ("#F3E8FF", "#7E22CE")
BADGE_CINZA = ("#F3F4F6", "#4B5563")


# Cor sólida de cada situação do quarto (barra de proporção da tela inicial).
COR_SITUACAO_QUARTO = {
    "Disponível": VERDE,
    "Ocupado": AZUL,
    "Reservado": AMARELO,
    "Manutenção": VERMELHO,
}

# Cores dos alertas da tela inicial, por nível (mesmos pares dos badges).
ESTILO_NIVEL_ALERTA = {
    "critico": BADGE_VERMELHO,
    "aviso": BADGE_AMARELO,
    "info": BADGE_AZUL,
}


def estilo_badge_status(valor):
    """Retorna cores semânticas para status conhecidos; desconhecidos ficam como texto."""
    estilos = {
        "Confirmada": BADGE_AZUL,
        "Hospedada": BADGE_VERDE,
        "Finalizada": BADGE_CINZA,
        "Cancelada": BADGE_VERMELHO,
        "Não compareceu": BADGE_AMARELO,
        "Pago": BADGE_VERDE,
        "Parcial": BADGE_AMARELO,
        "Pendente": BADGE_AMARELO,
        "A reembolsar": BADGE_ROXO,
        "Valor retido": BADGE_ROXO,
        "Quitada": BADGE_VERDE,
        "A vencer": BADGE_AZUL,
        "Vencida": BADGE_VERMELHO,
        "Vence hoje": BADGE_AMARELO,
        "Agendado": BADGE_AZUL,
        "Em andamento": BADGE_VERDE,
        "Encerrado": BADGE_CINZA,
        "Disponível": BADGE_VERDE,
        "Ocupado": BADGE_AZUL,
        "Reservado": BADGE_AMARELO,
        "Manutenção": BADGE_VERMELHO,
        "Ativo": BADGE_VERDE,
        "Inativo": BADGE_CINZA,
        "Entrada": BADGE_VERDE,
        "Saída": BADGE_VERMELHO,
    }
    if valor in estilos:
        return estilos[valor]
    if valor.startswith("Vencida há "):
        return BADGE_VERMELHO
    return None
