import customtkinter as ctk
from tkinter import messagebox
from src.repositories.usuario_repository import UsuarioRepository
repo = UsuarioRepository()  

class TelaLogin(ctk.CTk):
    def __init__(self, on_sucesso):
        super().__init__()
        self.title("Pousada – Login")
        self.geometry("1280x800")
        self.resizable(False, False)
        self.on_sucesso = on_sucesso

        # Título
        self.label = ctk.CTkLabel(self, text="Gestão de Hotel", font=("Helvetica", 22, "bold"))
        self.label.pack(pady=30)

        # Campo Email
        self.entry_email = ctk.CTkEntry(self, placeholder_text="E-mail", width=280, height=45)
        self.entry_email.pack(pady=10)

        # Campo Senha
        self.entry_senha = ctk.CTkEntry(self, placeholder_text="Senha", width=280, height=45, show="*")
        self.entry_senha.pack(pady=10)

        # Botão Entrar
        self.btn_entrar = ctk.CTkButton(self, text="Entrar", width=280, height=45, command=self.verificar_login)
        self.btn_entrar.pack(pady=20)

    def verificar_login(self):
        email = self.entry_email.get()
        senha = self.entry_senha.get()
        
        usuario_logado = repo.validar_login(email, senha)
        if usuario_logado:
            self.destroy()      # Fecha a janela de login
            self.on_sucesso()   # Callback para abrir o App principal
        else:
            messagebox.showerror("Erro de Autenticação", "E-mail ou senha incorretos.")