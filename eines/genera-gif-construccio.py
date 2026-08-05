#!/usr/bin/env python3
"""
Genera el GIF animat «En construcció» del bàner de la portada.

    python3 eines/genera-gif-construccio.py

Crea dos fitxers a assets/img/:
    en-construccio.gif   — animat (franges que llisquen + triangles que
                           parpellegen, com un llum d'obres)
    en-construccio.png   — imatge fixa, per a qui té activada la reducció de
                           moviment al sistema operatiu

L'animació és cíclica perfecta: les franges es desplacen exactament un període
al llarg de tots els fotogrames, de manera que en tornar a començar no se'n
nota el salt.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── Aspecte ─────────────────────────────────────────────────────────────────
AMPLADA = 2400
ALTURA = 122

GROC = (245, 166, 35)
GROC_APAGAT = (120, 84, 20)     # triangles quan el llum és «apagat»
NEGRE = (26, 26, 26)
NEGRE_PLACA = (10, 8, 10)

MARGE_FRANGES = 15          # gruix de la franja de perill a dalt i a baix
GRUIX_FRANJA = 15           # gruix de cada banda diagonal
FOTOGRAMES = 12
MIL·LISEGONS = 80           # durada de cada fotograma
COLORS = 4                  # només hi ha groc, dos negres i la vora

TEXT = 'EN CONSTRUCCIÓ'
ESPAIAT = 11                # espai extra entre lletres

RUTA_FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def carrega_font(mida: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(RUTA_FONT, mida)
    except OSError:
        return ImageFont.load_default()


def dibuixa_franges(dibuix: ImageDraw.ImageDraw, desplacament: int,
                    periode: int) -> None:
    """Franges diagonals de perill que cobreixen tota la imatge."""
    # Cada banda va de baix a dalt amb pendent 45°, de manera que el
    # desplaçament horitzontal la fa lliscar cap a la dreta.
    primera = -((ALTURA // periode) + 2) * periode
    x = primera + desplacament
    while x < AMPLADA + ALTURA + periode:
        dibuix.line([(x, ALTURA), (x + ALTURA, 0)], fill=GROC, width=GRUIX_FRANJA)
        x += periode


def dibuixa_triangle(dibuix: ImageDraw.ImageDraw, cx: int, cy: int,
                     mida: int, encès: bool) -> None:
    """Senyal triangular d'advertiment amb una exclamació a dins."""
    color = GROC if encès else GROC_APAGAT
    h = mida * math.sqrt(3) / 2
    dibuix.polygon(
        [(cx, cy - h / 2), (cx - mida / 2, cy + h / 2), (cx + mida / 2, cy + h / 2)],
        outline=color, width=max(3, mida // 12)
    )
    gruix = max(3, mida // 11)
    dibuix.line([(cx, cy - h / 6), (cx, cy + h / 8)], fill=color, width=gruix)
    r = gruix * 0.7
    dibuix.ellipse([cx - r, cy + h / 4 - r, cx + r, cy + h / 4 + r], fill=color)


def text_espaiat(dibuix: ImageDraw.ImageDraw, x: int, y: int, text: str,
                 font: ImageFont.FreeTypeFont, color) -> int:
    """Escriu el text lletra a lletra per poder-ne separar els caràcters."""
    for lletra in text:
        dibuix.text((x, y), lletra, font=font, fill=color)
        x += round(dibuix.textlength(lletra, font=font)) + ESPAIAT
    return x


def amplada_text(dibuix: ImageDraw.ImageDraw, text: str,
                 font: ImageFont.FreeTypeFont) -> int:
    total = sum(round(dibuix.textlength(l, font=font)) + ESPAIAT for l in text)
    return total - ESPAIAT


def fotograma(index: int, periode: int) -> Image.Image:
    imatge = Image.new('RGB', (AMPLADA, ALTURA), NEGRE)
    dibuix = ImageDraw.Draw(imatge)

    desplacament = round(index / FOTOGRAMES * periode)
    dibuixa_franges(dibuix, desplacament, periode)

    # Placa central fosca on va el text.
    dibuix.rectangle([0, MARGE_FRANGES, AMPLADA, ALTURA - MARGE_FRANGES],
                     fill=NEGRE_PLACA)

    font = carrega_font(60)
    ample_text = amplada_text(dibuix, TEXT, font)

    mida_triangle = 54
    separacio = 44          # entre triangle i text

    total = (mida_triangle + separacio + ample_text + separacio + mida_triangle)
    inici = (AMPLADA - total) // 2
    centre_y = ALTURA // 2

    # Els triangles parpellegen a la meitat del cicle, com un llum d'obres.
    # (No hi posem cap barra vertical al costat del text: a aquesta mida es
    # llegiria com una lletra més.)
    encès = index < FOTOGRAMES // 2

    dibuixa_triangle(dibuix, inici + mida_triangle // 2, centre_y,
                     mida_triangle, encès)

    caixa = dibuix.textbbox((0, 0), TEXT, font=font)
    y_text = centre_y - (caixa[3] + caixa[1]) // 2
    text_espaiat(dibuix, inici + mida_triangle + separacio, y_text,
                 TEXT, font, GROC)

    dibuixa_triangle(dibuix, inici + total - mida_triangle // 2, centre_y,
                     mida_triangle, encès)

    return imatge


def paleta_fixa() -> Image.Image:
    """
    Paleta global del GIF. A més dels quatre colors plans hi posem uns tons
    intermedis, perquè les vores suavitzades del text i dels triangles no
    quedin dentades en reduir els colors.
    """
    def barreja(a, b, factor):
        return tuple(round(x + (y - x) * factor) for x, y in zip(a, b))

    colors = [
        NEGRE_PLACA,
        NEGRE,
        GROC,
        GROC_APAGAT,
        barreja(NEGRE_PLACA, GROC, 0.35),
        barreja(NEGRE_PLACA, GROC, 0.7),
        barreja(NEGRE_PLACA, GROC_APAGAT, 0.5),
        barreja(NEGRE, GROC, 0.5),
    ]

    paleta = Image.new('P', (1, 1))
    pla = [component for color in colors for component in color]
    pla += [0] * (768 - len(pla))
    paleta.putpalette(pla)
    return paleta


def main() -> None:
    periode = round(2 * GRUIX_FRANJA * math.sqrt(2))
    fotogrames = [fotograma(i, periode) for i in range(FOTOGRAMES)]

    desti = Path(__file__).resolve().parent.parent / 'assets' / 'img'
    desti.mkdir(parents=True, exist_ok=True)

    gif = desti / 'en-construccio.gif'
    # Paleta fixa i disposal=1: així cada fotograma només desa el tros que
    # canvia respecte de l'anterior (les franges), i el fitxer baixa a la
    # meitat. La paleta ha de ser la mateixa per a tots els fotogrames, perquè
    # el GIF n'ha de fer servir una de global.
    paleta = paleta_fixa()
    reduits = [f.quantize(palette=paleta, dither=Image.Dither.NONE)
               for f in fotogrames]
    reduits[0].save(
        gif,
        save_all=True,
        append_images=reduits[1:],
        duration=MIL·LISEGONS,
        loop=0,
        optimize=True,
        disposal=1,
    )

    png = desti / 'en-construccio.png'
    fotogrames[0].save(png, optimize=True)

    verifica(gif, fotogrames)

    print(f'GIF  : {gif}  ({gif.stat().st_size // 1024} KB, '
          f'{FOTOGRAMES} fotogrames, {AMPLADA}x{ALTURA})')
    print(f'PNG  : {png}  ({png.stat().st_size // 1024} KB) — versió fixa')


def verifica(gif: Path, esperats: list[Image.Image]) -> None:
    """
    Amb disposal=1 cada fotograma es dibuixa damunt de l'anterior. Cal
    comprovar que en reproduir-lo se'n recompon bé cadascun i que no hi queda
    cap rastre del fotograma previ.
    """
    from PIL import ImageChops, ImageSequence

    llegits = [f.convert('RGB')
               for f in ImageSequence.Iterator(Image.open(gif))]

    if len(llegits) != len(esperats):
        raise AssertionError(f'{len(llegits)} fotogrames en lloc de {len(esperats)}')

    pitjor = 0
    for i, (llegit, esperat) in enumerate(zip(llegits, esperats)):
        diferencia = ImageChops.difference(llegit, esperat.convert('RGB'))
        caixa = diferencia.getbbox()
        if caixa is None:
            continue
        # La quantificació a 4 colors pot moure algun píxel de les vores del
        # text; el que no s'admet és que quedi cap regió gran diferent.
        histograma = diferencia.convert('L').histogram()
        pixels = sum(histograma[41:])
        proporcio = pixels / (AMPLADA * ALTURA)
        pitjor = max(pitjor, proporcio)
        if proporcio > 0.01:
            raise AssertionError(
                f'el fotograma {i} es recompon malament '
                f'({proporcio:.1%} de píxels diferents)')

    print(f'Verificació: OK — els {len(llegits)} fotogrames es recomponen '
          f'(desviació màxima {pitjor:.2%})')


if __name__ == '__main__':
    main()
