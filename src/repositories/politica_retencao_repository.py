from datetime import datetime

from database.conexao import inserir, consultar_um, consultar_todos
from src.models.politica_retencao import PoliticaRetencao

FORMATO_DATA_HORA = dict(sep=" ", timespec="seconds")


class PoliticaRetencaoRepository:
    """Histórico da regra de retenção: a definição mais recente vale; nenhuma é alterada."""

    def _para_objeto(self, linha):
        if linha is None:
            return None
        return PoliticaRetencao(
            id=linha["id"], dias_antecedencia=linha["dias_antecedencia"],
            percentual_cancelamento_tardio=linha["percentual_cancelamento_tardio"],
            percentual_no_show=linha["percentual_no_show"], usuario_id=linha["usuario_id"],
            definido_em=datetime.fromisoformat(linha["definido_em"]))

    def definir(self, politica, conexao=None):
        politica.definido_em = politica.definido_em or datetime.now().replace(microsecond=0)
        politica.id = inserir(
            """INSERT INTO politica_retencao
               (dias_antecedencia, percentual_cancelamento_tardio, percentual_no_show,
                usuario_id, definido_em)
               VALUES (?, ?, ?, ?, ?)""",
            (politica.dias_antecedencia, politica.percentual_cancelamento_tardio,
             politica.percentual_no_show, politica.usuario_id,
             politica.definido_em.isoformat(**FORMATO_DATA_HORA)),
            conexao=conexao)
        return politica

    def vigente(self):
        """A definição mais recente, ou None se a administração nunca definiu a regra."""
        return self._para_objeto(
            consultar_um("SELECT * FROM politica_retencao ORDER BY id DESC LIMIT 1"))

    def buscar_por_id(self, politica_id):
        return self._para_objeto(
            consultar_um("SELECT * FROM politica_retencao WHERE id = ?", (politica_id,)))

    def historico(self):
        """Todas as definições, da mais recente para a mais antiga."""
        return [self._para_objeto(l) for l in
                consultar_todos("SELECT * FROM politica_retencao ORDER BY id DESC")]
