import customtkinter as ctk

from src.utils.pousada import NOME_POUSADA
from src.utils.permissoes import rotulo_perfil
from src.utils.sessao import Sessao
from ui.componentes.icones_menu import icone
from ui.estilos import AZUL, COR_MENU, COR_MENU_HOVER, VERMELHO_HOVER, fonte

LARGURA_MENU = 260

COR_TEXTO = "#F9FAFB"
COR_TEXTO_SECUNDARIO = "#9CA3AF"
COR_BORDA = "#374151"
COR_PERFIL_FUNDO = "#111827"

# (nome da tela, permissão necessária — None = todos os perfis)
GRUPOS_MENU = {
    "GERAL": [
        ("Início", None),
    ],
    "HOSPEDAGEM": [
        ("Hóspedes", "hospedes.ver"),
        ("Histórico de hospedagem", "hospedes.ver"),
        ("Quartos", "quartos.ver"),
        ("Reservas", "reservas.ver"),
        ("Check-in / Check-out", "reservas.checkin"),
    ],
    "FINANCEIRO": [
        ("Despesas", "despesas.gerenciar"),
        ("Caixa", "caixa.ver"),
        ("Relatórios", "relatorios.ver"),
    ],
    "ADMINISTRAÇÃO": [
        ("Usuários", "usuarios.gerenciar"),
    ],
}


def grupos_permitidos():
    """Grupos do menu com as telas que o usuário logado pode abrir."""
    grupos = []
    for grupo, itens in GRUPOS_MENU.items():
        nomes = [
            nome for nome, permissao in itens
            if permissao is None or Sessao.pode(permissao)
        ]
        if nomes:
            grupos.append((grupo, nomes))
    return grupos


def itens_permitidos():
    """Telas que o usuário logado pode abrir, na ordem do menu."""
    return [nome for _, nomes in grupos_permitidos() for nome in nomes]


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


class ItemMenu(ctk.CTkFrame):
    def __init__(self, master, nome, comando):
        super().__init__(master, fg_color="transparent", corner_radius=8, height=42)
        self.pack_propagate(False)

        self._icone_inativo = icone(nome, COR_TEXTO_SECUNDARIO)
        self._icone_ativo = icone(nome, "#FFFFFF")

        self.indicador = ctk.CTkFrame(self, width=3, corner_radius=3, fg_color="transparent")
        self.indicador.pack(side="left", fill="y", padx=(0, 5))

        self.botao = ctk.CTkButton(
            self,
            text=f"  {nome}" if self._icone_inativo else nome,
            image=self._icone_inativo,
            compound="left",
            anchor="w",
            height=38,
            corner_radius=8,
            font=fonte(13, True),
            fg_color="transparent",
            hover_color=COR_MENU_HOVER,
            text_color=COR_TEXTO_SECUNDARIO,
            command=comando,
        )
        self.botao.pack(side="left", fill="both", expand=True)

    def destacar(self, ativo):
        if ativo:
            self.indicador.configure(fg_color=AZUL)
            self.botao.configure(
                fg_color=AZUL,
                hover_color=AZUL,
                text_color="#FFFFFF",
                image=self._icone_ativo,
            )
        else:
            self.indicador.configure(fg_color="transparent")
            self.botao.configure(
                fg_color="transparent",
                hover_color=COR_MENU_HOVER,
                text_color=COR_TEXTO_SECUNDARIO,
                image=self._icone_inativo,
            )


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
        ctk.CTkLabel(
            avatar,
            text=_iniciais(usuario.nome),
            text_color="white",
            font=fonte(14, True),
            fg_color="transparent",
        ).place(relx=0.5, rely=0.5, anchor="center")

        textos = ctk.CTkFrame(topo, fg_color="transparent")
        textos.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(
            textos,
            text=_nome_curto(usuario.nome),
            font=fonte(13, True),
            text_color="white",
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            textos,
            text=f"  {rotulo_perfil(usuario.perfil)}  ",
            font=fonte(11, True),
            text_color="white",
            fg_color=AZUL,
            corner_radius=8,
            height=20,
        ).pack(anchor="w", pady=(4, 0))

        acoes = ctk.CTkFrame(self, fg_color="transparent")
        acoes.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkButton(
            acoes,
            text="Alterar senha",
            height=30,
            corner_radius=8,
            font=fonte(12),
            fg_color="transparent",
            border_width=1,
            border_color="#4B5563",
            hover_color=COR_MENU_HOVER,
            text_color="#E5E7EB",
            command=ao_alterar_senha,
        ).pack(fill="x")
        ctk.CTkButton(
            acoes,
            text="Sair",
            height=30,
            corner_radius=8,
            font=fonte(12),
            fg_color="transparent",
            border_width=1,
            border_color="#4B5563",
            hover_color=VERMELHO_HOVER,
            text_color="#E5E7EB",
            command=ao_sair,
        ).pack(fill="x", pady=(6, 0))


class MenuLateral(ctk.CTkFrame):
    def __init__(self, master, ao_navegar, ao_alterar_senha, ao_sair):
        super().__init__(master, width=LARGURA_MENU, fg_color=COR_MENU, corner_radius=0)
        self.pack_propagate(False)

        self._botoes = {}

        # cabeçalho
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", padx=22, pady=(25, 20))

        ctk.CTkLabel(
            cabecalho,
            text=NOME_POUSADA,
            font=fonte(19, True),
            text_color=COR_TEXTO,
            anchor="w",
            justify="left",
            wraplength=LARGURA_MENU - 44,
        ).pack(anchor="w")

        ctk.CTkLabel(
            cabecalho,
            text="SISTEMA DE GESTÃO",
            font=fonte(10, True),
            text_color=COR_TEXTO_SECUNDARIO,
            anchor="w",
        ).pack(anchor="w", pady=(5, 0))

        ctk.CTkFrame(self, height=1, fg_color=COR_BORDA).pack(fill="x", padx=16)

        # área de navegação com rolagem
        area_navegacao = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COR_BORDA,
            scrollbar_button_hover_color=COR_TEXTO_SECUNDARIO,
            corner_radius=0,
        )
        area_navegacao.pack(fill="both", expand=True, padx=10, pady=12)

        for grupo, nomes in grupos_permitidos():
            ctk.CTkLabel(
                area_navegacao,
                text=grupo,
                font=fonte(10, True),
                text_color=COR_TEXTO_SECUNDARIO,
                anchor="w",
            ).pack(fill="x", padx=10, pady=(17, 7))

            for nome in nomes:
                item = ItemMenu(area_navegacao, nome, comando=lambda n=nome: ao_navegar(n))
                item.pack(fill="x", pady=2)
                self._botoes[nome] = item

        if Sessao.usuario is not None:
            self.perfil = PerfilMini(self, Sessao.usuario, ao_alterar_senha, ao_sair)
            self.perfil.pack(side="bottom", fill="x", padx=12, pady=14)

    def destacar(self, ativo):
        for nome, item in self._botoes.items():
            item.destacar(nome == ativo)