"""Ícones do menu lateral, desenhados em código (sem arquivos de imagem).

Cada ícone é desenhado numa grade de 24x24 em traço fino e arredondado, numa cor só. Cores e
tamanhos diferentes saem do mesmo desenho (`desenhar`), então o item ativo e o inativo combinam.
"""
import math

import customtkinter as ctk
from PIL import Image, ImageDraw

GRADE = 24          # o desenho é feito numa grade de 24x24...
ESCALA = 8          # ...ampliada 8x e reduzida depois, para as bordas ficarem suaves
TRACO = 2           # espessura do traço, em unidades da grade
LADO_PADRAO = 20    # tamanho do ícone na tela, em pixels

_cache = {}


def _linha(d, pontos, cor, junta=True):
    e = ESCALA
    pts = [(x * e, y * e) for x, y in pontos]
    d.line(pts, fill=cor, width=TRACO * e, joint="curve" if junta else None)
    for x, y in pts:                              # pontas arredondadas
        r = TRACO * e / 2
        d.ellipse((x - r, y - r, x + r, y + r), fill=cor)


def _caixa(caixa):
    return tuple(v * ESCALA for v in caixa)


def _contorno(d, caixa, cor, raio=2):
    d.rounded_rectangle(_caixa(caixa), radius=raio * ESCALA, outline=cor, width=TRACO * ESCALA)


def _circulo(d, caixa, cor, cheio=False):
    if cheio:
        d.ellipse(_caixa(caixa), fill=cor)
    else:
        d.ellipse(_caixa(caixa), outline=cor, width=TRACO * ESCALA)


def _inicio(d, c):
    _linha(d, [(3, 11), (12, 3), (21, 11)], c)
    _linha(d, [(5.5, 9.5), (5.5, 20), (18.5, 20), (18.5, 9.5)], c)
    _linha(d, [(10, 20), (10, 14), (14, 14), (14, 20)], c)


def _arco(d, cx, cy, rx, ry, de, ate, cor, passos=24):
    """Traço curvo: pedaço de elipse de `de` a `ate` graus (0 = direita, 270 = topo)."""
    pontos = [(cx + rx * math.cos(math.radians(de + (ate - de) * i / passos)),
               cy + ry * math.sin(math.radians(de + (ate - de) * i / passos)))
              for i in range(passos + 1)]
    _linha(d, pontos, cor)


def _pessoa(d, c, cx=12.0, escala=1.0, so_direita=False):
    r = 3.7 * escala
    topo = 4.5 if escala == 1 else 5.5
    _circulo(d, (cx - r, topo, cx + r, topo + 2 * r), c)
    base, rx, ry = 21.0, 8.0 * escala, 7.5 * escala
    _arco(d, cx, base, rx, ry, 270 if so_direita else 180, 360, c)


def _hospedes(d, c):
    _pessoa(d, c)


def _historico(d, c):
    _circulo(d, (3, 3, 21, 21), c)
    _linha(d, [(12, 7), (12, 12), (15.5, 14)], c)


def _quartos(d, c):
    _linha(d, [(3, 5), (3, 19)], c)                       # cabeceira
    _linha(d, [(3, 16), (21, 16), (21, 19)], c)           # colchão e pé da cama
    _contorno(d, (6, 9.5, 11.5, 13.5), c, raio=1.5)       # travesseiro
    _linha(d, [(14.5, 12.5), (21, 12.5), (21, 16)], c)    # cobertor


def _reservas(d, c):
    _contorno(d, (3, 5, 21, 21), c, raio=3)
    _linha(d, [(3, 10), (21, 10)], c)
    _linha(d, [(8, 2.5), (8, 6.5)], c)
    _linha(d, [(16, 2.5), (16, 6.5)], c)
    _linha(d, [(8, 15), (8.1, 15)], c)
    _linha(d, [(12, 15), (12.1, 15)], c)
    _linha(d, [(16, 15), (16.1, 15)], c)


def _checkin(d, c):
    _linha(d, [(14, 4), (19, 4), (19, 20), (14, 20)], c)
    _linha(d, [(3, 12), (15, 12)], c)
    _linha(d, [(10.5, 7.5), (15, 12), (10.5, 16.5)], c)


def _despesas(d, c):
    _linha(d, [(5, 3), (5, 21), (8.3, 19), (11.7, 21), (15, 19), (18.4, 21), (19, 21), (19, 3), (5, 3)], c)
    _linha(d, [(9, 9), (15, 9)], c)
    _linha(d, [(9, 13), (13, 13)], c)


def _caixa_(d, c):
    _contorno(d, (2.5, 6, 21.5, 18), c, raio=2.5)
    _circulo(d, (9, 9, 15, 15), c)
    _linha(d, [(5.5, 12), (5.6, 12)], c)
    _linha(d, [(18.4, 12), (18.5, 12)], c)


def _relatorios(d, c):
    _linha(d, [(3, 3), (3, 21), (21, 21)], c)
    _linha(d, [(8, 17), (8, 12)], c)
    _linha(d, [(13, 17), (13, 7)], c)
    _linha(d, [(18, 17), (18, 10)], c)


def _usuarios(d, c):
    _pessoa(d, c, cx=9.0, escala=0.82)
    _circulo(d, (14.8, 5.5, 20.2, 10.9), c)               # segunda pessoa, atrás
    _arco(d, 17.5, 21, 5.2, 7.5, 270, 360, c)


DESENHOS = {
    "Início": _inicio,
    "Hóspedes": _hospedes,
    "Histórico de hospedagem": _historico,
    "Quartos": _quartos,
    "Reservas": _reservas,
    "Check-in / Check-out": _checkin,
    "Despesas": _despesas,
    "Caixa": _caixa_,
    "Relatórios": _relatorios,
    "Usuários": _usuarios,
}


def desenhar(nome, cor, lado=LADO_PADRAO):
    """Imagem PIL (RGBA) do ícone, com `lado` pixels de lado, ou None se o item não tem ícone."""
    desenho = DESENHOS.get(nome)
    if desenho is None:
        return None
    tela = GRADE * ESCALA
    imagem = Image.new("RGBA", (tela, tela), (0, 0, 0, 0))
    desenho(ImageDraw.Draw(imagem), cor)
    return imagem.resize((lado * 2, lado * 2), Image.LANCZOS)    # 2x: nítido em telas de alta densidade


def icone(nome, cor, lado=LADO_PADRAO):
    """CTkImage do ícone na cor pedida (guardado em cache), ou None se o item não tem ícone."""
    chave = (nome, cor, lado)
    if chave not in _cache:
        imagem = desenhar(nome, cor, lado)
        _cache[chave] = (None if imagem is None
                         else ctk.CTkImage(light_image=imagem, size=(lado, lado)))
    return _cache[chave]
