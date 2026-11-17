"""Regras da tela de check-in / check-out (funções puras, sem banco e sem interface)."""
from src.models.checkin import MovimentoDoDia
from src.utils.constantes import (MOVIMENTO_CHECKIN, MOVIMENTO_CHECKOUT, RESERVA_CONFIRMADA,
                                  RESERVA_HOSPEDADA)
from src.utils.filtros import normalizar_texto, parece_numerico
from src.utils.formatacao import apenas_digitos


def _dias(n):
    return f"{n} dia" if n == 1 else f"{n} dias"


def chegadas(reservas, hoje):
    """Confirmadas (sem check-in) com entrada prevista até hoje; as mais antigas primeiro.

    Entrada já vencida continua aqui: o hóspede ainda pode chegar (ou a reserva vira no-show).
    """
    lista = [r for r in reservas if r.situacao == RESERVA_CONFIRMADA and r.data_entrada <= hoje]
    return sorted(lista, key=lambda r: (r.data_entrada, r.id or 0))


def hospedados(reservas):
    """Hospedadas, com a saída prevista mais próxima (ou já vencida) primeiro."""
    lista = [r for r in reservas if r.situacao == RESERVA_HOSPEDADA]
    return sorted(lista, key=lambda r: (r.data_saida, r.id or 0))


def rotulo_chegada(reserva, hoje):
    """'Hoje' ou 'Atrasada há N dia(s)'."""
    atraso = (hoje - reserva.data_entrada).days
    return "Hoje" if atraso <= 0 else f"Atrasada há {_dias(atraso)}"


def rotulo_saida(reserva, hoje):
    """'Atrasada há N dia(s)', 'Sai hoje', 'Sai amanhã' ou 'Sai em N dias'."""
    falta = (reserva.data_saida - hoje).days
    if falta < 0:
        return f"Atrasada há {_dias(-falta)}"
    if falta == 0:
        return "Sai hoje"
    return "Sai amanhã" if falta == 1 else f"Sai em {falta} dias"


def movimentos_do_dia(reservas, hoje):
    """Check-ins e check-outs feitos hoje (pelo horário real), do mais recente ao mais antigo."""
    movimentos = []
    for r in reservas:
        if r.checkin_em is not None and r.checkin_em.date() == hoje:
            movimentos.append(MovimentoDoDia(MOVIMENTO_CHECKIN, r, r.checkin_em))
        if r.checkout_em is not None and r.checkout_em.date() == hoje:
            movimentos.append(MovimentoDoDia(MOVIMENTO_CHECKOUT, r, r.checkout_em))
    return sorted(movimentos, key=lambda m: m.quando, reverse=True)


def filtrar(reservas, termo, hospedes, quartos):
    """Reservas cujo código, hóspede, CPF ou quarto batem com o texto (sem acento nem maiúsculas).

    hospedes / quartos: {id: objeto}. Texto vazio devolve tudo.
    """
    termo = (termo or "").strip()
    if not termo:
        return list(reservas)
    texto = normalizar_texto(termo)
    digitos = apenas_digitos(termo) if parece_numerico(termo) else ""
    achadas = []
    for r in reservas:
        hospede, quarto = hospedes.get(r.hospede_id), quartos.get(r.quarto_id)
        campos = [f"{r.id:04d}", normalizar_texto(hospede.nome) if hospede else "",
                  normalizar_texto(quarto.numero) if quarto else ""]
        achou = any(texto in campo for campo in campos)
        if not achou and digitos and hospede:
            achou = digitos in apenas_digitos(hospede.cpf)
        if achou:
            achadas.append(r)
    return achadas
