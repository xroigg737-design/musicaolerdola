#!/usr/bin/env python3
"""
Prepara les imatges de fons de la portada a partir de l'original quadrat.

    python3 eines/genera-hero.py [ruta/de/l/original.jpeg]

Per defecte busca l'original a ~/Downloads/olerdola/Best.jpeg (a la carpeta de
Windows). L'original és quadrat (2048x2048) i el hero és panoràmic, així que en
fem dos retalls triats a mà:

  · hero-olerdola.jpg        16:9 — pantalles amples. Retall vertical al 35 %,
                             que és el que deixa el campanar sencer i, a la
                             vegada, no talla el teclat del piano.
  · hero-olerdola-mobil.jpg  3:4  — mòbils en vertical. Retall horitzontal al
                             40 %, que manté el violoncel i la glicina.

Es desen en JPEG progressiu: és una fotografia, i en PNG pesava 2,4 MB.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ORIGEN_PER_DEFECTE = Path(
    '/mnt/c/Users/xroig/Downloads/olerdola/Best.jpeg'
)

# (nom, relació amplada/alçada, posició del retall, amplada final)
#
# Les amplades són a consciència: la foto té molt detall de fullatge i a
# 1920 px no baixava de 390 KB. Com que el hero va sempre darrere un filtre
# d'enfosquiment i un degradat, a 1680 px no es nota la diferència i pesa 90 KB
# menys. La versió de mòbil és de 900 px, que amb pantalles de 400 punts i el
# doble de densitat ja va sobrada.
RETALLS = [
    ('hero-olerdola.jpg',       16 / 9, 0.35, 1680),
    ('hero-olerdola-mobil.jpg',  3 / 4, 0.40,  900),
]

QUALITAT = 82


def retalla(src: Image.Image, relacio: float, posicio: float) -> Image.Image:
    """
    Retalla al format demanat. La posició (0..1) diu on es col·loca la finestra
    dins de l'excedent: en formats amples mou el retall amunt o avall, i en
    formats verticals l'esquerra o la dreta.
    """
    ample, alt = src.size
    if relacio >= ample / alt:
        # Més ample que l'original: retallem verticalment.
        nou_alt = round(ample / relacio)
        y = round((alt - nou_alt) * posicio)
        return src.crop((0, y, ample, y + nou_alt))

    # Més estret que l'original: retallem horitzontalment.
    nou_ample = round(alt * relacio)
    x = round((ample - nou_ample) * posicio)
    return src.crop((x, 0, x + nou_ample, alt))


def main() -> int:
    origen = Path(sys.argv[1]) if len(sys.argv) > 1 else ORIGEN_PER_DEFECTE
    if not origen.is_file():
        print(f'No trobo l\'original a {origen}', file=sys.stderr)
        print('Passa\'n la ruta com a argument.', file=sys.stderr)
        return 1

    src = Image.open(origen).convert('RGB')
    desti = Path(__file__).resolve().parent.parent / 'assets' / 'img'
    desti.mkdir(parents=True, exist_ok=True)

    print(f'Original : {origen.name}  {src.size[0]}x{src.size[1]}  '
          f'({origen.stat().st_size // 1024} KB)')

    for nom, relacio, posicio, ample_final in RETALLS:
        tallada = retalla(src, relacio, posicio)
        alt_final = round(ample_final / relacio)
        final = tallada.resize((ample_final, alt_final), Image.LANCZOS)

        ruta = desti / nom
        final.save(ruta, 'JPEG', quality=QUALITAT, optimize=True,
                   progressive=True, subsampling=1)
        print(f'  {nom:26} {ample_final}x{alt_final}  '
              f'{ruta.stat().st_size // 1024} KB')

    return 0


if __name__ == '__main__':
    sys.exit(main())
