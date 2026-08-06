#!/usr/bin/env python3
"""
Prepara les imatges de fons de la portada a partir de l'original quadrat.

    python3 eines/genera-hero.py [ruta/de/l/original.jpeg]

Per defecte busca l'original a ~/Downloads/olerdola/Best.jpeg (a la carpeta de
Windows). L'original és quadrat (2048x2048) i el hero és panoràmic, així que en
fem dos retalls triats a mà:

  · hero-olerdola        16:9 — pantalles amples. Retall vertical al 35 %,
                         que és el que deixa el campanar sencer i, a la
                         vegada, no talla el teclat del piano.
  · hero-olerdola-mobil  3:4  — mòbils en vertical. Retall horitzontal al
                         40 %, que manté el violoncel i la glicina.

De cada retall se'n desen dues versions, WebP i JPEG progressiu. El WebP és el
que serveix el navegador (la meitat de pes amb més detall) i el JPEG hi és
només com a recanvi; el CSS els ofereix tots dos amb image-set().
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ORIGEN_PER_DEFECTE = Path(
    '/mnt/c/Users/xroig/Downloads/olerdola/Best.jpeg'
)

# (nom base, relació amplada/alçada, posició del retall, amplada final)
#
# La portada ja no va darrere cap filtre d'enfosquiment, o sigui que el detall
# de la foto es veu tal com és i val la pena servir-la gran: 1920 px per a les
# pantalles amples i 1080 px per als mòbils en vertical (400 punts a densitat
# doble o triple). En WebP pesen com el JPEG petit d'abans.
RETALLS = [
    ('hero-olerdola',        16 / 9, 0.35, 1920),
    ('hero-olerdola-mobil',   3 / 4, 0.40, 1080),
]

QUALITAT_JPEG = 82
QUALITAT_WEBP = 78

# Realçat que es fa a la imatge, un cop reduïda:
#
#  · L'enfocament recupera el detall del fullatge i de la pedra que es perd en
#    reduir amb LANCZOS. Va abans del color perquè treballa sobre la lluminositat.
#    No pugis del 55 %: cada punt de més infla el WebP, perquè la foto ja és
#    tota fullatge i el realçat li afegeix detall fi a cada branca.
#  · El contrast i la saturació donen cos a la posta de sol. Són suaus a
#    consciència: el gruix del realçat el fa el CSS, que és on es pot ajustar
#    sense tornar a generar els fitxers.
ENFOCAMENT = dict(radius=1.2, percent=55, threshold=3)
CONTRAST = 1.06
SATURACIO = 1.08


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

        final = final.filter(ImageFilter.UnsharpMask(**ENFOCAMENT))
        final = ImageEnhance.Contrast(final).enhance(CONTRAST)
        final = ImageEnhance.Color(final).enhance(SATURACIO)

        # El JPEG només el veu qui no té WebP, o sigui gairebé ningú; per això
        # va a una qualitat més continguda que el WebP.
        ruta_jpg = desti / f'{nom}.jpg'
        final.save(ruta_jpg, 'JPEG', quality=QUALITAT_JPEG, optimize=True,
                   progressive=True, subsampling=1)

        ruta_webp = desti / f'{nom}.webp'
        final.save(ruta_webp, 'WEBP', quality=QUALITAT_WEBP, method=6)

        print(f'  {nom:26} {ample_final}x{alt_final}  '
              f'webp {ruta_webp.stat().st_size // 1024} KB  ·  '
              f'jpg {ruta_jpg.stat().st_size // 1024} KB')

    return 0


if __name__ == '__main__':
    sys.exit(main())
