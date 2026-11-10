from datetime import date, datetime

from database.conexao import inserir, executar, consultar_um, consultar_todos
from src.models.reserva import Reserva
from src.utils.constantes import (RESERVA_CANCELADA, RESERVA_CONFIRMADA, RESERVA_FINALIZADA,
                                  RESERVA_HOSPEDADA, RESERVA_NO_SHOW)

FORMATO_DATA_HORA = dict(sep=" ", timespec="seconds")


def _data_hora(valor):
    return datetime.fromisoformat(valor) if valor else None


class ReservaRepository:

    def _para_objeto(self, linha):
        if linha is None:
            return None
        return Reserva(
            id=linha["id"],
            hospede_id=linha["hospede_id"],
            quarto_id=linha["quarto_id"],
            data_entrada=date.fromisoformat(linha["data_entrada"]),
            data_saida=date.fromisoformat(linha["data_saida"]),
            valor_diaria=linha["valor_diaria"],
            valor_total=linha["valor_total"],
            situacao=linha["situacao"],
            checkin_em=_data_hora(linha["checkin_em"]),
            checkin_por=linha["checkin_por"],
            checkout_em=_data_hora(linha["checkout_em"]),
            checkout_por=linha["checkout_por"],
            criada_em=_data_hora(linha["criada_em"]),
            cancelada_em=_data_hora(linha["cancelada_em"]),
            cancelada_por=linha["cancelada_por"],
            cancelamento_motivo=linha["cancelamento_motivo"],
            noshow_em=_data_hora(linha["noshow_em"]),
            noshow_por=linha["noshow_por"],
        )

    def _para_objetos(self, linhas):
        return [self._para_objeto(linha) for linha in linhas]

    def criar(self, reserva, conexao=None):
        # toda reserva guarda quando foi criada: se quem chamou não informou, é agora
        if reserva.criada_em is None:
            reserva.criada_em = datetime.now().replace(microsecond=0)
        reserva.id = inserir(
            """INSERT INTO reservas
               (hospede_id, quarto_id, data_entrada, data_saida,
                valor_diaria, valor_total, situacao, criada_em,
                checkin_em, checkin_por, checkout_em, checkout_por,
                cancelada_em, cancelada_por, cancelamento_motivo, noshow_em, noshow_por)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                reserva.hospede_id,
                reserva.quarto_id,
                reserva.data_entrada.isoformat(),
                reserva.data_saida.isoformat(),
                reserva.valor_diaria,
                reserva.valor_total,
                reserva.situacao,
                reserva.criada_em.isoformat(**FORMATO_DATA_HORA),
                reserva.checkin_em.isoformat(**FORMATO_DATA_HORA) if reserva.checkin_em else None,
                reserva.checkin_por,
                reserva.checkout_em.isoformat(**FORMATO_DATA_HORA) if reserva.checkout_em else None,
                reserva.checkout_por,
                reserva.cancelada_em.isoformat(**FORMATO_DATA_HORA) if reserva.cancelada_em else None,
                reserva.cancelada_por,
                reserva.cancelamento_motivo,
                reserva.noshow_em.isoformat(**FORMATO_DATA_HORA) if reserva.noshow_em else None,
                reserva.noshow_por,
            ),
            conexao=conexao,
        )
        return reserva

    def buscar_por_id(self, reserva_id):
        linha = consultar_um("SELECT * FROM reservas WHERE id = ?", (reserva_id,))
        return self._para_objeto(linha)

    def listar(self):
        linhas = consultar_todos("SELECT * FROM reservas ORDER BY data_entrada DESC")
        return self._para_objetos(linhas)

    def listar_por_hospede(self, hospede_id):
        linhas = consultar_todos(
            "SELECT * FROM reservas WHERE hospede_id = ? ORDER BY data_entrada DESC",
            (hospede_id,),
        )
        return self._para_objetos(linhas)

    def listar_por_quarto(self, quarto_id):
        linhas = consultar_todos(
            "SELECT * FROM reservas WHERE quarto_id = ? ORDER BY data_entrada DESC",
            (quarto_id,),
        )
        return self._para_objetos(linhas)

    def listar_conflitantes(self, quarto_id, data_entrada, data_saida, ignorar_id=None):
        """Reservas confirmadas ou hospedadas do quarto que se sobrepõem ao período.
        Só consulta. Quem decide o que fazer com isso é o service."""
        linhas = consultar_todos(
            """SELECT * FROM reservas
               WHERE quarto_id = ?
                 AND situacao IN (?, ?)
                 AND data_entrada < ?
                 AND data_saida > ?
                 AND id != ?""",
            (quarto_id, RESERVA_CONFIRMADA, RESERVA_HOSPEDADA,
             data_saida.isoformat(), data_entrada.isoformat(), ignorar_id or -1),
        )
        return self._para_objetos(linhas)

    def atualizar(self, reserva, conexao=None):
        afetadas = executar(
            """UPDATE reservas
               SET hospede_id = ?, quarto_id = ?, data_entrada = ?, data_saida = ?,
                   valor_diaria = ?, valor_total = ?, situacao = ?
               WHERE id = ?""",
            (
                reserva.hospede_id,
                reserva.quarto_id,
                reserva.data_entrada.isoformat(),
                reserva.data_saida.isoformat(),
                reserva.valor_diaria,
                reserva.valor_total,
                reserva.situacao,
                reserva.id,
            ),
            conexao=conexao,
        )
        return afetadas > 0

    def registrar_checkin(self, reserva_id, quando, usuario_id, conexao=None):
        """Marca a reserva como hospedada e grava quando e por quem foi feito o check-in.

        Só age se a reserva ainda está confirmada e sem check-in; devolve False se não agiu.
        As datas previstas (data_entrada e data_saida) não são tocadas.
        """
        afetadas = executar(
            """UPDATE reservas SET situacao = ?, checkin_em = ?, checkin_por = ?
               WHERE id = ? AND situacao = ? AND checkin_em IS NULL""",
            (RESERVA_HOSPEDADA, quando.isoformat(**FORMATO_DATA_HORA), usuario_id,
             reserva_id, RESERVA_CONFIRMADA),
            conexao=conexao,
        )
        return afetadas > 0

    def registrar_checkout(self, reserva_id, quando, usuario_id, conexao=None):
        """Finaliza a reserva e grava quando e por quem foi feito o check-out.

        Só age se a reserva está hospedada e ainda sem check-out; devolve False se não agiu.
        """
        afetadas = executar(
            """UPDATE reservas SET situacao = ?, checkout_em = ?, checkout_por = ?
               WHERE id = ? AND situacao = ? AND checkout_em IS NULL""",
            (RESERVA_FINALIZADA, quando.isoformat(**FORMATO_DATA_HORA), usuario_id,
             reserva_id, RESERVA_HOSPEDADA),
            conexao=conexao,
        )
        return afetadas > 0

    def registrar_cancelamento(self, reserva_id, quando, usuario_id, motivo, conexao=None):
        """Cancela a reserva e grava quando, por quem e por que foi cancelada.

        Só age se a reserva ainda está confirmada; devolve False se não agiu.
        """
        afetadas = executar(
            """UPDATE reservas
               SET situacao = ?, cancelada_em = ?, cancelada_por = ?, cancelamento_motivo = ?
               WHERE id = ? AND situacao = ?""",
            (RESERVA_CANCELADA, quando.isoformat(**FORMATO_DATA_HORA), usuario_id, motivo,
             reserva_id, RESERVA_CONFIRMADA),
            conexao=conexao,
        )
        return afetadas > 0

    def registrar_no_show(self, reserva_id, quando, usuario_id, conexao=None):
        """Marca a reserva como 'Não compareceu' e grava quando e por quem foi marcada.

        Só age se a reserva ainda está confirmada; devolve False se não agiu.
        """
        afetadas = executar(
            """UPDATE reservas SET situacao = ?, noshow_em = ?, noshow_por = ?
               WHERE id = ? AND situacao = ?""",
            (RESERVA_NO_SHOW, quando.isoformat(**FORMATO_DATA_HORA), usuario_id,
             reserva_id, RESERVA_CONFIRMADA),
            conexao=conexao,
        )
        return afetadas > 0
