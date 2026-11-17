"""Identidade da pousada nos relatórios e documentos (cabeçalho padrão)."""
from pathlib import Path

# Troque aqui o nome e o arquivo do logotipo: todos os relatórios (e as exportações) usam estes dois.
NOME_POUSADA = "Pousada"
ARQUIVO_LOGO = Path(__file__).resolve().parents[2] / "assets" / "logo.png"
