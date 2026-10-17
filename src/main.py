from database.conexao import inicializar_banco
from ui.app import App

if __name__ == "__main__":
    inicializar_banco()
    App().run()