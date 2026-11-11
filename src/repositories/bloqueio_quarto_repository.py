from datetime import datetime, time, timedelta

from database.conexao import consultar_todos, consultar_um, inserir
from src.models.bloqueio_quarto import BloqueioQuarto

FORMATO_DATA_HORA = dict(sep=" ", timespec="seconds")


def _texto(momento):
    return momento.isoformat(**FORMATO_DATA_HORA)


class BloqueioQuartoRepository:

    def _para_objeto(self, linha):
        if linha is None:
            return None
        return BloqueioQuarto(
            id=linha["id"],
            quarto_id=linha["quarto_id"],
            inicio=datetime.fromisoformat(linha["inicio"]),
            fim=datetime.fromisoformat(linha["fim"]),
            motivo=linha["motivo"],
            usuario_id=linha["usuario_id"],
            criado_em=datetime.fromisoformat(linha["criado_em"]),
        )

    def _para_objetos(self, linhas):
        return [self._para_objeto(linha) for linha in linhas]

    def criar(self, bloqueio, conexao=None):
        # todo bloqueio guarda quando foi registrado: se quem chamou não informou, é agora
        if bloqueio.criado_em is None:
            bloqueio.criado_em = datetime.now().replace(microsecond=0)
        bloqueio.id = inserir(
            """INSERT INTO bloqueios_quarto (quarto_id, inicio, fim, motivo, usuario_id, criado_em)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (bloqueio.quarto_id, _texto(bloqueio.inicio), _texto(bloqueio.fim),
             bloqueio.motivo, bloqueio.usuario_id, _texto(bloqueio.criado_em)),
            conexao=conexao,
        )
        return bloqueio

    def buscar_por_id(self, bloqueio_id):
        linha = consultar_um("SELECT * FROM bloqueios_quarto WHERE id = ?", (bloqueio_id,))
        return self._para_objeto(linha)

    def listar(self, quarto_id=None, periodo_de=None, periodo_ate=None):
        """Histórico, do bloqueio mais recente para o mais antigo.

        quarto_id:   só os bloqueios desse quarto (None = todos os quartos)
        periodo_de / periodo_ate: datas (limites incluídos); traz os bloqueios que tocam esse
                     intervalo, mesmo que tenham começado antes ou terminem depois dele
        """
        condicoes, parametros = [], []
        if quarto_id is not None:
            condicoes.append("quarto_id = ?")
            parametros.append(quarto_id)
        if periodo_de is not None:
            condicoes.append("fim > ?")
            parametros.append(_texto(datetime.combine(periodo_de, time.min)))
        if periodo_ate is not None:
            condicoes.append("inicio < ?")
            parametros.append(_texto(datetime.combine(periodo_ate + timedelta(days=1), time.min)))
        where = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
        linhas = consultar_todos(
            f"SELECT * FROM bloqueios_quarto {where} ORDER BY inicio DESC, id DESC", parametros)
        return self._para_objetos(linhas)

    def listar_sobrepostos(self, inicio, fim, quarto_id=None):
        """Bloqueios que se sobrepõem ao intervalo [inicio, fim).

        Quem termina exatamente quando o outro começa não se sobrepõe.
        quarto_id: só desse quarto (None = qualquer quarto)
        """
        sql = "SELECT * FROM bloqueios_quarto WHERE inicio < ? AND fim > ?"
        parametros = [_texto(fim), _texto(inicio)]
        if quarto_id is not None:
            sql += " AND quarto_id = ?"
            parametros.append(quarto_id)
        return self._para_objetos(consultar_todos(sql + " ORDER BY inicio", parametros))

    def existe_por_quarto(self, quarto_id):
        return consultar_um("SELECT 1 FROM bloqueios_quarto WHERE quarto_id = ? LIMIT 1",
                            (quarto_id,)) is not None
