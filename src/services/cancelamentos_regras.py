"""Regras do relatório de cancelamentos e no-show (funções puras)."""
from src.services.pagamento_regras import arredondar
from src.utils.constantes import RESERVA_CANCELADA, RESERVA_NO_SHOW
from src.utils.filtros import normalizar_texto, parece_numerico
from src.utils.formatacao import apenas_digitos


def calcular(registro):
    """Preenche pago_liquido e a_reembolsar de um RegistroCancelamento e devolve ele.

    pago_liquido é o que o hotel tem em mãos (pagamentos - reembolsos). a_reembolsar é o que
    ainda deve ao hóspede: pago_liquido - valor_retido (nunca negativo); fica None quando a
    retenção não foi registrada (reserva cancelada antes de existir a regra).
    """
    registro.pago_liquido = arredondar(registro.pago_bruto - registro.reembolsado)
    registro.a_reembolsar = (None if registro.valor_retido is None
                             else max(arredondar(registro.pago_liquido - registro.valor_retido),
                                      0.0))
    return registro


def filtrar_por_texto(registros, termo):
    """Registros cujo hóspede, CPF, quarto ou código da reserva batem com o termo."""
    termo = (termo or "").strip()
    if not termo:
        return list(registros)
    texto = normalizar_texto(termo)
    digitos = apenas_digitos(termo) if parece_numerico(termo) else ""
    resultado = []
    for r in registros:
        campos = [f"{r.reserva_id:04d}", normalizar_texto(r.hospede), normalizar_texto(r.quarto)]
        achou = any(texto in campo for campo in campos)
        if not achou and digitos:
            achou = digitos in apenas_digitos(r.cpf)
        if achou:
            resultado.append(r)
    return resultado


def totalizar(registros):
    """Somas da lista. Registros sem retenção registrada ficam de fora dos totais de valores."""
    com_retencao = [r for r in registros if r.valor_retido is not None]
    return {
        "cancelamentos": sum(r.situacao == RESERVA_CANCELADA for r in registros),
        "no_shows": sum(r.situacao == RESERVA_NO_SHOW for r in registros),
        "valor_reservas": arredondar(sum(r.valor_total for r in registros)),
        "total_pago": arredondar(sum(r.pago_bruto for r in registros)),
        "total_retido": arredondar(sum(r.valor_retido for r in com_retencao)),
        "total_reembolsado": arredondar(sum(r.reembolsado for r in registros)),
        "total_a_reembolsar": arredondar(sum(r.a_reembolsar for r in com_retencao)),
        "sem_retencao_registrada": len(registros) - len(com_retencao),
    }
