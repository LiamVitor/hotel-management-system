import customtkinter as ctk

from src.utils.permissoes import ADMIN, GERENTE, RECEPCIONISTA, rotulo_perfil
from src.utils.sessao import Sessao
from ui.estilos import AZUL, COR_MENU, COR_MENU_HOVER, VERMELHO, VERMELHO_HOVER, fonte

# (nome da tela, permissão necessária — None = todos os perfis)
ITENS_MENU = [
    ("Início", None),
    ("Hóspedes", "hospedes.ver"),
    ("Histórico de hospedagem", "hospedes.ver"),
    ("Quartos", "quartos.ver"),
    ("Reservas", "reservas.ver"),
    ("Check-in / Check-out", "reservas.checkin"),
    ("Despesas", "despesas.gerenciar"),
    ("Caixa", "caixa.ver"),
    ("Relatórios", "relatorios.ver"),
    ("Usuários", "usuarios.gerenciar"),
]

COR_PERFIL_FUNDO = "#111827"

def itens_permitidos():
    """Telas que o usuário logado pode abrir, na ordem do menu."""
    return [nome for nome, permissao in ITENS_MENU
            if permissao is None or Sessao.pode(permissao)]


def _iniciais(nome):
    partes = nome.split()
    if not partes:
        return "?"
    if len(partes) == 1:
        return partes[0][0].upper()
    return (partes[0][0] + partes[-1][0]).upper()


def _nome_curto(nome, limite=18):
    partes = nome.split()
    texto = nome if len(partes) < 3 else f"{partes[0]} {partes[-1]}"
    return texto if len(texto) <= limite else texto[:limite - 1] + "…"


class PerfilMini(ctk.CTkFrame):
    """Cartão no fim do menu: quem está logado, o perfil de acesso e as ações da conta."""

    def __init__(self, master, usuario, ao_alterar_senha, ao_sair):
        super().__init__(master, fg_color=COR_PERFIL_FUNDO, corner_radius=12)

        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(12, 8))
        # avatar redondo: quadro de tamanho fixo com as iniciais centralizadas
        avatar = ctk.CTkFrame(topo, width=44, height=44, corner_radius=22, fg_color=AZUL)
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=_iniciais(usuario.nome), text_color="white",
                     font=fonte(14, True), fg_color="transparent"
                     ).place(relx=0.5, rely=0.5, anchor="center")
        textos = ctk.CTkFrame(topo, fg_color="transparent")
        textos.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(textos, text=_nome_curto(usuario.nome), font=fonte(13, True),
                     text_color="white", anchor="w").pack(anchor="w")
        ctk.CTkLabel(textos, text=f"  {rotulo_perfil(usuario.perfil)}  ", font=fonte(11, True),
                     text_color="white", fg_color=AZUL, corner_radius=8, height=20
                     ).pack(anchor="w", pady=(4, 0))

        acoes = ctk.CTkFrame(self, fg_color="transparent")
        acoes.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkButton(acoes, text="Alterar senha", height=30, corner_radius=8, font=fonte(12),
                      fg_color="transparent", border_width=1, border_color="#4B5563",
                      hover_color=COR_MENU_HOVER, text_color="#E5E7EB",
                      command=ao_alterar_senha).pack(fill="x")
        ctk.CTkButton(acoes, text="Sair", height=30, corner_radius=8, font=fonte(12),
                      fg_color="transparent", border_width=1, border_color="#4B5563",
                      hover_color=VERMELHO_HOVER, text_color="#E5E7EB",
                      command=ao_sair).pack(fill="x", pady=(6, 0))


class MenuLateral(ctk.CTkFrame):
    def __init__(self, master, ao_navegar, ao_alterar_senha, ao_sair):
        super().__init__(master, width=240, fg_color=COR_MENU, corner_radius=0)
        self.pack_propagate(False)
        ctk.CTkLabel(self, text="Pousada", font=fonte(22, True), text_color="white"
                     ).pack(anchor="w", padx=24, pady=(28, 24))

        self._botoes = {}
        for nome in itens_permitidos():
            botao = ctk.CTkButton(self, text=nome, anchor="w", height=42, corner_radius=8,
                                  fg_color="transparent", hover_color=COR_MENU_HOVER,
                                  text_color="#E5E7EB", font=fonte(14),
                                  command=lambda n=nome: ao_navegar(n))
            botao.pack(fill="x", padx=12, pady=2)
            self._botoes[nome] = botao

        if Sessao.usuario is not None:
            self.perfil = PerfilMini(self, Sessao.usuario, ao_alterar_senha, ao_sair)
            self.perfil.pack(side="bottom", fill="x", padx=12, pady=16)

    def destacar(self, ativo):
        for nome, botao in self._botoes.items():
            if nome == ativo:
                botao.configure(fg_color=AZUL, hover_color=AZUL)
            else:
                botao.configure(fg_color="transparent", hover_color=COR_MENU_HOVER)
