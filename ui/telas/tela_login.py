import customtkinter as ctk
from src.services.erros import ErroNegocio
from src.services.usuario_service import UsuarioService

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class TelaLogin(ctk.CTk):
    LARGURA = 420
    ALTURA = 560

    def __init__(self, on_sucesso=None):
        super().__init__()
        self.servico = UsuarioService()
        self.on_sucesso = on_sucesso      # opcional: funcao(usuario) chamada após o login
        self.usuario_logado = None        # fica com o usuário se o login der certo

        self.title("Pousada – Login")
        self._centralizar(self.LARGURA, self.ALTURA)
        self.resizable(False, False)

        card = ctk.CTkFrame(self, corner_radius=16)
        card.pack(expand=True, fill="both", padx=30, pady=30)

        ctk.CTkLabel(
            card, text="Gestão de Hotel",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(pady=(45, 4))
        ctk.CTkLabel(
            card, text="Entre com suas credenciais", text_color="gray",
        ).pack(pady=(0, 30))

        self.entry_usuario = ctk.CTkEntry(
            card, placeholder_text="Usuário", width=280, height=45,
        )
        self.entry_usuario.pack(pady=8)

        self.entry_senha = ctk.CTkEntry(
            card, placeholder_text="Senha", width=280, height=45, show="•",
        )
        self.entry_senha.pack(pady=8)

        self.var_mostrar = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            card, text="Mostrar senha",
            variable=self.var_mostrar, command=self._alternar_senha,
        ).pack(anchor="w", padx=(40, 0), pady=(6, 0))

        self.label_erro = ctk.CTkLabel(card, text="", text_color="#e74c3c", wraplength=280)
        self.label_erro.pack(pady=(12, 0))

        self.btn_entrar = ctk.CTkButton(
            card, text="Entrar", width=280, height=45,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.verificar_login,
        )
        self.btn_entrar.pack(pady=(10, 0))

        self.bind("<Return>", lambda _e: self.verificar_login())
        self.after(200, self.entry_usuario.focus)

    def _centralizar(self, largura, altura):
        x = (self.winfo_screenwidth() - largura) // 2
        y = (self.winfo_screenheight() - altura) // 2
        self.geometry(f"{largura}x{altura}+{x}+{y}")

    def _alternar_senha(self):
        self.entry_senha.configure(show="" if self.var_mostrar.get() else "•")

    def _mostrar_erro(self, mensagem):
        self.label_erro.configure(text=mensagem)

    def verificar_login(self):
        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get()

        if not usuario or not senha:
            self._mostrar_erro("Preencha o usuário e a senha.")
            return

        self.btn_entrar.configure(state="disabled", text="Entrando...")
        self.update_idletasks()

        try:
            logado = self.servico.autenticar(usuario, senha)
            erro = "" if logado else "Usuário ou senha incorretos."
        except ErroNegocio as problema:   # conta desativada
            logado, erro = None, str(problema)

        if logado:
            self.usuario_logado = logado
            self.destroy()
            if self.on_sucesso:
                self.on_sucesso(logado)
        else:
            self.btn_entrar.configure(state="normal", text="Entrar")
            self.entry_senha.delete(0, "end")
            self.entry_senha.focus()
            self._mostrar_erro(erro)