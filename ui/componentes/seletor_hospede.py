"""Seletor de hóspede com busca: o mesmo campo usado na tela de Reservas e no Histórico."""
from src.utils.formatacao import formatar_cpf, formatar_telefone
from ui.componentes.seletor import CampoSeletor, JanelaSelecao

COLUNAS_SELECAO_HOSPEDE = [("Nome", "nome", 230), ("CPF", "cpf", 130),
                           ("Telefone", "telefone", 140), ("E-mail", "email", 200)]


def texto_hospede(h):
    """Texto mostrado no campo depois de escolher: 'Nome — CPF'."""
    return f"{h.nome} — {formatar_cpf(h.cpf)}"


class CampoSeletorHospede(CampoSeletor):
    """Campo que abre a janela de busca de hóspedes (por nome, CPF, telefone ou e-mail).

    valor() devolve o id do hóspede escolhido (ou None). atualizar() confere se ele ainda
    existe e refaz o texto, caso o cadastro tenha sido editado ou excluído em outra tela.
    """

    def __init__(self, master, servicos, rotulo="Hóspede", ao_mudar=None):
        super().__init__(master, rotulo, "Clique para pesquisar e escolher o hóspede…",
                         self._abrir_selecao, ao_mudar)
        self._servicos = servicos

    def _abrir_selecao(self, escolher):
        def buscar(termo, _opcao):
            return [{"id": h.id, "nome": h.nome, "cpf": formatar_cpf(h.cpf),
                     "telefone": formatar_telefone(h.telefone), "email": h.email or "",
                     "texto": texto_hospede(h)}
                    for h in self._servicos.hospedes.listar(termo)]

        JanelaSelecao(self, "Selecionar hóspede", COLUNAS_SELECAO_HOSPEDE, buscar,
                      lambda linha: escolher(linha["id"], linha["texto"]),
                      placeholder="Buscar por nome, CPF, telefone ou e-mail")

    def atualizar(self):
        """Devolve o hóspede escolhido, atualizado (None se foi excluído; o campo é limpo)."""
        if self.valor() is None:
            return None
        hospede = self._servicos.hospedes.buscar_por_id(self.valor())
        if hospede is None:
            self.limpar(notificar=False)
        else:
            self.definir(hospede.id, texto_hospede(hospede), notificar=False)
        return hospede
