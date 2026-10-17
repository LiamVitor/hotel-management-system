"""Popula o banco com dados de exemplo (só se ele estiver vazio).

Uso, na raiz do projeto:  python -m database.seed
"""
from datetime import date, timedelta

from database.conexao import inicializar_banco
from src.models.hospede import Hospede
from src.models.quarto import Quarto
from src.models.reserva import Reserva
from src.repositories.hospede_repository import HospedeRepository
from src.repositories.quarto_repository import QuartoRepository
from src.repositories.reserva_repository import ReservaRepository

HOSPEDES = [
    ("Maria Silva Santos", "123.456.789-00", "(86) 99912-3456", "maria.silva@email.com"),
    ("João Pedro Almeida", "234.567.890-11", "(86) 98801-2233", "joao.almeida@email.com"),
    ("Ana Beatriz Costa", "345.678.901-22", "(86) 99655-4421", "ana.costa@email.com"),
    ("Carlos Eduardo Lima", "456.789.012-33", "(86) 98877-1020", "carlos.lima@email.com"),
    ("Fernanda Oliveira Rocha", "567.890.123-44", "(86) 99430-7788", "fernanda.rocha@email.com"),
    ("Ricardo Mendes Souza", "678.901.234-55", "(86) 98122-9090", "ricardo.souza@email.com"),
]

QUARTOS = [  # número, tipo, capacidade, diária, situação
    ("101", "Solteiro", 1, 120.0, "Disponível"),
    ("102", "Casal", 2, 180.0, "Reservado"),
    ("103", "Casal", 2, 180.0, "Ocupado"),
    ("201", "Suíte", 2, 280.0, "Ocupado"),
    ("202", "Família", 4, 350.0, "Reservado"),
    ("203", "Solteiro", 1, 120.0, "Disponível"),
    ("204", "Casal", 2, 190.0, "Manutenção"),
    ("301", "Suíte", 3, 320.0, "Disponível"),
]

RESERVAS = [  # hóspede (posição), quarto (número), dias até entrada, dias até saída, situação
    (0, "102", 0, 3, "Confirmada"),
    (1, "201", -2, 1, "Hospedada"),
    (2, "202", 0, 2, "Confirmada"),
    (3, "103", -1, 0, "Hospedada"),
    (4, "301", 2, 5, "Confirmada"),
    (5, "101", -5, -2, "Finalizada"),
    (0, "203", -10, -8, "Finalizada"),
    (1, "102", 10, 12, "Cancelada"),
    (2, "101", -12, -9, "Finalizada"),
    (3, "102", -4, -1, "Finalizada"),
    (4, "202", -6, -3, "Finalizada"),
]


def popular():
    inicializar_banco()
    repo_h, repo_q, repo_r = HospedeRepository(), QuartoRepository(), ReservaRepository()
    if repo_h.listar() or repo_q.listar() or repo_r.listar():
        print("O banco já tem dados. Nada foi alterado.")
        return

    hospedes = [repo_h.criar(Hospede(nome=n, cpf=c, telefone=t, email=e))
                for n, c, t, e in HOSPEDES]
    quartos = {numero: repo_q.criar(Quarto(numero=numero, tipo=tipo, capacidade=cap,
                                           preco_diaria=preco, situacao=situacao))
               for numero, tipo, cap, preco, situacao in QUARTOS}

    hoje = date.today()
    for pos, numero, ini, fim, situacao in RESERVAS:
        quarto = quartos[numero]
        entrada, saida = hoje + timedelta(days=ini), hoje + timedelta(days=fim)
        repo_r.criar(Reserva(
            hospede_id=hospedes[pos].id, quarto_id=quarto.id,
            data_entrada=entrada, data_saida=saida,
            valor_diaria=quarto.preco_diaria,
            valor_total=(saida - entrada).days * quarto.preco_diaria,
            situacao=situacao))
    print(f"Banco populado: {len(hospedes)} hóspedes, {len(quartos)} quartos, "
          f"{len(RESERVAS)} reservas.")


if __name__ == "__main__":
    popular()
