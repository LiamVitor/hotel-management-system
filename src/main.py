from database.conexao import inicializar_banco
from ui.app import App
from ui.telas.tela_login import TelaLogin

def iniciar_sistema_principal():
    app = App()
    app.run()


if __name__ == "__main__":
    inicializar_banco()
    login = TelaLogin(on_sucesso=iniciar_sistema_principal)
    login.mainloop()