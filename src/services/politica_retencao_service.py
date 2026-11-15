import math

from src.models.politica_retencao import PoliticaRetencao
from src.repositories.politica_retencao_repository import PoliticaRetencaoRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.services.erros import ErroNegocio
from src.utils.constantes import RETENCAO_DIAS_MAX
from src.utils.sessao import Sessao


class PoliticaRetencaoService:
    """Regra de retenção definida pela administração (só o administrador altera).

    Cada alteração vira uma nova definição no histórico, com quem fez e quando; a mais recente
    vale daí em diante. Cancelamentos e no-shows já registrados guardam a retenção calculada
    na época e não mudam.
    """

    def __init__(self, repo=None, usuario_repo=None):
        self.repo = repo or PoliticaRetencaoRepository()
        self.usuario_repo = usuario_repo or UsuarioRepository()

    def vigente(self):
        """A regra em vigor, ou None se a administração ainda não definiu (nada é retido)."""
        return self.repo.vigente()

    def definir(self, dias_antecedencia, percentual_cancelamento_tardio, percentual_no_show):
        """Define a regra: dias de antecedência e % retido em cancelamento tardio e em no-show."""
        Sessao.exigir("retencao.configurar")
        if (isinstance(dias_antecedencia, bool) or not isinstance(dias_antecedencia, int)
                or not 0 <= dias_antecedencia <= RETENCAO_DIAS_MAX):
            raise ErroNegocio(
                f"Os dias de antecedência devem ser um número inteiro de 0 a {RETENCAO_DIAS_MAX}.")
        tardio = self._percentual(percentual_cancelamento_tardio, "do cancelamento tardio")
        no_show = self._percentual(percentual_no_show, "do no-show")
        return self.repo.definir(PoliticaRetencao(
            dias_antecedencia=dias_antecedencia, percentual_cancelamento_tardio=tardio,
            percentual_no_show=no_show, usuario_id=Sessao.usuario.id))

    def historico(self):
        """[(PoliticaRetencao, nome de quem definiu)], da definição mais recente para a mais antiga."""
        Sessao.exigir("relatorios.ver")
        nomes, resultado = {}, []
        for politica in self.repo.historico():
            if politica.usuario_id not in nomes:
                usuario = self.usuario_repo.buscar_por_id(politica.usuario_id)
                nomes[politica.usuario_id] = usuario.nome if usuario else "—"
            resultado.append((politica, nomes[politica.usuario_id]))
        return resultado

    @staticmethod
    def _percentual(valor, de_que):
        if (isinstance(valor, bool) or not isinstance(valor, (int, float))
                or not math.isfinite(valor) or not 0 <= valor <= 100):
            raise ErroNegocio(f"O percentual {de_que} deve estar entre 0 e 100.")
        return round(float(valor), 2)
