"""Validações de formato usadas pelos services."""
import re

# Parte local sem pontos no começo/fim ou repetidos; domínio com ao menos um ponto e
# terminação de 2+ letras (ex.: nome@email.com, nome@empresa.com.br).
EMAIL_RE = re.compile(
    r"^[A-Za-z0-9_%+-]+(?:\.[A-Za-z0-9_%+-]+)*"
    r"@(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}$"
)


def email_valido(email):
    return bool(EMAIL_RE.match((email or "").strip()))
