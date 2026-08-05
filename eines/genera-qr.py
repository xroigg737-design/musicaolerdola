#!/usr/bin/env python3
"""
Generador de codis QR sense dependències externes.

Escrit per al cartell de l'enquesta de l'Associació Amics de la Música
d'Olèrdola. Implementa la norma ISO/IEC 18004 en mode byte per a les
versions 1 a 6 (fins a 134 caràcters), que és de sobres per a una URL.

Ús:
    python3 eines/genera-qr.py                      # QR de l'enquesta
    python3 eines/genera-qr.py "text" sortida.png   # qualsevol altre text

El programa es verifica a si mateix: després de construir la matriu la
torna a llegir com ho faria un lector (llegint la informació de format,
desfent la màscara, desentrellaçant els blocs i comprovant que els
síndromes de Reed-Solomon són zero) i comprova que en surt el text original.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
#  Taules de la norma
# ═══════════════════════════════════════════════════════════════════════════

# Nombre total de paraules de codi (dades + correcció) per versió.
TOTAL_PARAULES = {1: 26, 2: 44, 3: 70, 4: 100, 5: 134, 6: 172}

# (paraules de correcció per bloc, nombre de blocs) per versió i nivell.
CORRECCIO = {
    1: {'L': (7, 1),  'M': (10, 1), 'Q': (13, 1), 'H': (17, 1)},
    2: {'L': (10, 1), 'M': (16, 1), 'Q': (22, 1), 'H': (28, 1)},
    3: {'L': (15, 1), 'M': (26, 1), 'Q': (18, 2), 'H': (22, 2)},
    4: {'L': (20, 1), 'M': (18, 2), 'Q': (26, 2), 'H': (16, 4)},
    5: {'L': (26, 1), 'M': (24, 2), 'Q': (18, 4), 'H': (22, 4)},
    6: {'L': (18, 2), 'M': (16, 4), 'Q': (24, 4), 'H': (28, 4)},
}

# Bits romanents que s'afegeixen al final del flux de dades.
ROMANENTS = {1: 0, 2: 7, 3: 7, 4: 7, 5: 7, 6: 7}

# Indicador de nivell de correcció dins la informació de format.
INDICADOR_NIVELL = {'L': 0b01, 'M': 0b00, 'Q': 0b11, 'H': 0b10}

# Ordre de preferència: com més amunt, més tolerància a taques i ratllades.
NIVELLS_PREFERITS = ('H', 'Q', 'M', 'L')


# ═══════════════════════════════════════════════════════════════════════════
#  Aritmètica al cos de Galois GF(256), amb polinomi primitiu 0x11D
# ═══════════════════════════════════════════════════════════════════════════

_EXP = [0] * 512
_LOG = [0] * 256


def _prepara_galois() -> None:
    x = 1
    for i in range(255):
        _EXP[i] = x
        _LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        _EXP[i] = _EXP[i - 255]


_prepara_galois()


def _mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def _poligen(n: int) -> list[int]:
    """Polinomi generador de Reed-Solomon per a n paraules de correcció."""
    g = [1]
    for i in range(n):
        nou = [0] * (len(g) + 1)
        for j, coef in enumerate(g):
            nou[j] ^= _mul(coef, 1)
            nou[j + 1] ^= _mul(coef, _EXP[i])
        g = nou
    return g


def correccio_reed_solomon(dades: list[int], n_correccio: int) -> list[int]:
    """Paraules de correcció d'errors per a un bloc de dades."""
    g = _poligen(n_correccio)
    residu = list(dades) + [0] * n_correccio
    for i in range(len(dades)):
        coef = residu[i]
        if coef == 0:
            continue
        for j, gc in enumerate(g):
            residu[i + j] ^= _mul(gc, coef)
    return residu[len(dades):]


def sindromes(bloc: list[int], n_correccio: int) -> list[int]:
    """Síndromes del bloc. Si totes són zero, el bloc és correcte."""
    resultat = []
    for i in range(n_correccio):
        s = 0
        for coef in bloc:
            s = _mul(s, _EXP[i]) ^ coef
        resultat.append(s)
    return resultat


# ═══════════════════════════════════════════════════════════════════════════
#  Codificació de les dades
# ═══════════════════════════════════════════════════════════════════════════

def tria_versio(n_bytes: int) -> tuple[int, str]:
    """Versió més petita possible i, dins d'aquesta, el nivell més robust."""
    for versio in sorted(TOTAL_PARAULES):
        for nivell in NIVELLS_PREFERITS:
            correccio, blocs = CORRECCIO[versio][nivell]
            paraules_dades = TOTAL_PARAULES[versio] - correccio * blocs
            # 4 bits de mode + 8 bits de longitud = 12 bits de capçalera
            if n_bytes * 8 + 12 <= paraules_dades * 8:
                return versio, nivell
    raise ValueError('El text és massa llarg per a les versions 1-6.')


def flux_de_dades(dades: bytes, versio: int, nivell: str) -> list[int]:
    """Paraules de codi de dades: capçalera, contingut, terminador i farciment."""
    correccio, blocs = CORRECCIO[versio][nivell]
    paraules_dades = TOTAL_PARAULES[versio] - correccio * blocs

    bits = '0100'                        # mode byte
    bits += format(len(dades), '08b')    # longitud (8 bits per a versions 1-9)
    bits += ''.join(format(b, '08b') for b in dades)

    capacitat = paraules_dades * 8
    bits += '0' * min(4, capacitat - len(bits))        # terminador
    bits += '0' * (-len(bits) % 8)                     # fins a byte sencer

    paraules = [int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)]

    # Farciment alternat, començant sempre per 0xEC.
    farciment = (0xEC, 0x11)
    i = 0
    while len(paraules) < paraules_dades:
        paraules.append(farciment[i % 2])
        i += 1
    return paraules


def reparteix_blocs(paraules: list[int], versio: int, nivell: str) -> list[list[int]]:
    """
    Divideix les paraules de dades en blocs segons la norma: els blocs del
    segon grup tenen exactament una paraula més que els del primer.
    """
    correccio, blocs = CORRECCIO[versio][nivell]
    total_dades = len(paraules)
    curtes = total_dades // blocs
    n_llargs = total_dades % blocs
    n_curts = blocs - n_llargs

    resultat, i = [], 0
    for _ in range(n_curts):
        resultat.append(paraules[i:i + curtes])
        i += curtes
    for _ in range(n_llargs):
        resultat.append(paraules[i:i + curtes + 1])
        i += curtes + 1
    assert i == total_dades
    return resultat


def entrellaça(blocs_dades: list[list[int]], n_correccio: int) -> list[int]:
    """Entrellaça les paraules de dades i després les de correcció."""
    blocs_correccio = [correccio_reed_solomon(b, n_correccio) for b in blocs_dades]

    sortida = []
    for i in range(max(len(b) for b in blocs_dades)):
        for bloc in blocs_dades:
            if i < len(bloc):
                sortida.append(bloc[i])
    for i in range(n_correccio):
        for bloc in blocs_correccio:
            sortida.append(bloc[i])
    return sortida


# ═══════════════════════════════════════════════════════════════════════════
#  Construcció de la matriu
# ═══════════════════════════════════════════════════════════════════════════

class Matriu:
    def __init__(self, versio: int):
        self.versio = versio
        self.mida = 17 + 4 * versio
        self.moduls = [[0] * self.mida for _ in range(self.mida)]
        self.funcional = [[False] * self.mida for _ in range(self.mida)]

    def posa(self, fila: int, col: int, valor: int, funcional: bool = True) -> None:
        self.moduls[fila][col] = valor
        if funcional:
            self.funcional[fila][col] = True

    def dibuixa_patrons(self) -> None:
        n = self.mida

        # Patrons de localització (7x7) amb els seus separadors.
        for base_f, base_c in ((0, 0), (0, n - 7), (n - 7, 0)):
            for df in range(-1, 8):
                for dc in range(-1, 8):
                    f, c = base_f + df, base_c + dc
                    if not (0 <= f < n and 0 <= c < n):
                        continue
                    vora = df in (0, 6) and 0 <= dc <= 6
                    vora |= dc in (0, 6) and 0 <= df <= 6
                    nucli = 2 <= df <= 4 and 2 <= dc <= 4
                    self.posa(f, c, 1 if (vora or nucli) else 0)

        # Patrons d'alineació (versions 2-6: dos centres).
        if self.versio >= 2:
            centres = [6, 4 * self.versio + 10]
            for cf in centres:
                for cc in centres:
                    # No es dibuixen damunt dels patrons de localització.
                    if self._xoca_amb_localitzacio(cf, cc):
                        continue
                    for df in range(-2, 3):
                        for dc in range(-2, 3):
                            anell = max(abs(df), abs(dc))
                            self.posa(cf + df, cc + dc, 1 if anell != 1 else 0)

        # Patrons de sincronisme.
        for i in range(8, n - 8):
            valor = 1 if i % 2 == 0 else 0
            self.posa(6, i, valor)
            self.posa(i, 6, valor)

        # Espai reservat per a la informació de format.
        for i in range(9):
            if not self.funcional[8][i]:
                self.posa(8, i, 0)
            if not self.funcional[i][8]:
                self.posa(i, 8, 0)
        for i in range(8):                 # fila 8, columnes n-1 … n-8
            self.posa(8, n - 1 - i, 0)
        for i in range(7):                 # columna 8, files n-1 … n-7
            self.posa(n - 1 - i, 8, 0)

        # Mòdul sempre fosc, a (4v+9, 8) = (n-8, 8). Va després de reservar
        # l'espai de format perquè aquell bucle no el trepitgi.
        self.posa(4 * self.versio + 9, 8, 1)

    def _xoca_amb_localitzacio(self, cf: int, cc: int) -> bool:
        n = self.mida
        for base_f, base_c in ((3, 3), (3, n - 4), (n - 4, 3)):
            if abs(cf - base_f) <= 4 and abs(cc - base_c) <= 4:
                return True
        return False

    def camí_de_dades(self) -> list[tuple[int, int]]:
        """Recorregut en ziga-zaga: columnes de dues en dues, de dreta a esquerra."""
        n = self.mida
        posicions = []
        col = n - 1
        amunt = True
        while col > 0:
            if col == 6:            # la columna de sincronisme se salta
                col -= 1
            files = range(n - 1, -1, -1) if amunt else range(n)
            for fila in files:
                for c in (col, col - 1):
                    if not self.funcional[fila][c]:
                        posicions.append((fila, c))
            col -= 2
            amunt = not amunt
        return posicions

    def escriu_dades(self, bits: str) -> None:
        posicions = self.camí_de_dades()
        assert len(posicions) == len(bits), \
            f'geometria incorrecta: {len(posicions)} mòduls per a {len(bits)} bits'
        for (fila, col), bit in zip(posicions, bits):
            self.moduls[fila][col] = int(bit)


def mascara(patro: int, fila: int, col: int) -> bool:
    match patro:
        case 0: return (fila + col) % 2 == 0
        case 1: return fila % 2 == 0
        case 2: return col % 3 == 0
        case 3: return (fila + col) % 3 == 0
        case 4: return (fila // 2 + col // 3) % 2 == 0
        case 5: return (fila * col) % 2 + (fila * col) % 3 == 0
        case 6: return ((fila * col) % 2 + (fila * col) % 3) % 2 == 0
        case 7: return ((fila + col) % 2 + (fila * col) % 3) % 2 == 0
    raise ValueError(patro)


def aplica_mascara(matriu: Matriu, patro: int) -> list[list[int]]:
    n = matriu.mida
    return [
        [
            matriu.moduls[f][c] ^ (1 if (not matriu.funcional[f][c]
                                         and mascara(patro, f, c)) else 0)
            for c in range(n)
        ]
        for f in range(n)
    ]


BCH_FORMAT = 0b10100110111
MASCARA_FORMAT = 0b101010000010010


def bits_de_format(nivell: str, patro: int) -> str:
    dades = (INDICADOR_NIVELL[nivell] << 3) | patro
    valor = dades << 10
    while valor.bit_length() > 10:
        valor ^= BCH_FORMAT << (valor.bit_length() - 11)
    return format(((dades << 10) | valor) ^ MASCARA_FORMAT, '015b')


def escriu_format(moduls: list[list[int]], nivell: str, patro: int) -> None:
    n = len(moduls)
    bits = bits_de_format(nivell, patro)
    # bit(i) = i-èsim bit començant pel menys significatiu
    b = [int(x) for x in reversed(bits)]

    for i in range(6):
        moduls[8][i] = b[i]
    moduls[8][7] = b[6]
    moduls[8][8] = b[7]
    moduls[7][8] = b[8]
    for i in range(9, 15):
        moduls[14 - i][8] = b[i]

    # Segona còpia: 7 mòduls avall a la columna 8 (el mòdul fosc de (n-8,8)
    # no en forma part) i 8 mòduls a la dreta de la fila 8.
    for i in range(7):
        moduls[n - 1 - i][8] = b[i]
    for i in range(7, 15):
        moduls[8][n - 15 + i] = b[i]


# ── Avaluació de les màscares (les quatre regles de penalització) ───────────

def penalitzacio(moduls: list[list[int]]) -> int:
    n = len(moduls)
    total = 0

    # Regla 1: sèries de 5 mòduls o més del mateix color.
    for linia in list(moduls) + [list(col) for col in zip(*moduls)]:
        seguits, anterior = 1, linia[0]
        for valor in linia[1:]:
            if valor == anterior:
                seguits += 1
            else:
                if seguits >= 5:
                    total += 3 + (seguits - 5)
                seguits, anterior = 1, valor
        if seguits >= 5:
            total += 3 + (seguits - 5)

    # Regla 2: blocs de 2x2 del mateix color.
    for f in range(n - 1):
        for c in range(n - 1):
            quadrat = (moduls[f][c], moduls[f][c + 1],
                       moduls[f + 1][c], moduls[f + 1][c + 1])
            if len(set(quadrat)) == 1:
                total += 3

    # Regla 3: patrons semblants al de localització (1:1:3:1:1 amb 4 clars).
    patrons = ([1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1])
    for linia in list(moduls) + [list(col) for col in zip(*moduls)]:
        for i in range(n - 10):
            tros = linia[i:i + 11]
            if tros in patrons:
                total += 40

    # Regla 4: desequilibri entre mòduls foscos i clars.
    foscos = sum(sum(f) for f in moduls)
    percentatge = foscos * 100 // (n * n)
    total += 10 * (abs(percentatge - 50) // 5)

    return total


# ═══════════════════════════════════════════════════════════════════════════
#  Generació completa
# ═══════════════════════════════════════════════════════════════════════════

def genera(text: str) -> tuple[list[list[int]], int, str, int]:
    dades = text.encode('utf-8')
    versio, nivell = tria_versio(len(dades))
    n_correccio, _ = CORRECCIO[versio][nivell]

    paraules = flux_de_dades(dades, versio, nivell)
    blocs = reparteix_blocs(paraules, versio, nivell)
    codificat = entrellaça(blocs, n_correccio)

    assert len(codificat) == TOTAL_PARAULES[versio], \
        f'{len(codificat)} paraules en lloc de {TOTAL_PARAULES[versio]}'

    bits = ''.join(format(p, '08b') for p in codificat) + '0' * ROMANENTS[versio]

    matriu = Matriu(versio)
    matriu.dibuixa_patrons()
    matriu.escriu_dades(bits)

    millor, millor_penalitzacio, millor_patro = None, None, 0
    for patro in range(8):
        candidat = aplica_mascara(matriu, patro)
        escriu_format(candidat, nivell, patro)
        p = penalitzacio(candidat)
        if millor_penalitzacio is None or p < millor_penalitzacio:
            millor, millor_penalitzacio, millor_patro = candidat, p, patro

    return millor, versio, nivell, millor_patro


# ═══════════════════════════════════════════════════════════════════════════
#  Verificació: tornem a llegir la matriu com ho faria un lector
# ═══════════════════════════════════════════════════════════════════════════

def llegeix(moduls: list[list[int]]) -> str:
    n = len(moduls)
    versio = (n - 17) // 4

    # 1. Informació de format (còpia principal, a la cantonada superior esquerra).
    crus = [moduls[8][i] for i in range(6)] + [moduls[8][7], moduls[8][8],
                                               moduls[7][8]] \
        + [moduls[14 - i][8] for i in range(9, 15)]
    valor = 0
    for i, bit in enumerate(crus):
        valor |= bit << i
    valor ^= MASCARA_FORMAT
    dades_format = valor >> 10
    nivell = {v: k for k, v in INDICADOR_NIVELL.items()}[dades_format >> 3]
    patro = dades_format & 0b111

    # La segona còpia de la informació de format es col·loca amb una fórmula
    # diferent: si les dues coincideixen, totes dues col·locacions són bones.
    segona = [moduls[n - 1 - i][8] for i in range(7)] \
        + [moduls[8][n - 15 + i] for i in range(7, 15)]
    valor2 = 0
    for i, bit in enumerate(segona):
        valor2 |= bit << i
    # «valor» ja té la màscara desfeta; cal desfer-la també a la segona còpia.
    if (valor2 ^ MASCARA_FORMAT) != valor:
        raise AssertionError('les dues còpies de la informació de format difereixen')

    # 2. Reconstruïm quins mòduls són funcionals i desfem la màscara.
    plantilla = Matriu(versio)
    plantilla.dibuixa_patrons()
    net = [
        [
            moduls[f][c] ^ (1 if (not plantilla.funcional[f][c]
                                  and mascara(patro, f, c)) else 0)
            for c in range(n)
        ]
        for f in range(n)
    ]

    # 3. Llegim el flux de bits pel mateix camí en ziga-zaga.
    bits = ''.join(str(net[f][c]) for f, c in plantilla.camí_de_dades())
    paraules = [int(bits[i:i + 8], 2)
                for i in range(0, TOTAL_PARAULES[versio] * 8, 8)]

    # 4. Desentrellacem i comprovem els síndromes de Reed-Solomon.
    n_correccio, n_blocs = CORRECCIO[versio][nivell]
    total_dades = TOTAL_PARAULES[versio] - n_correccio * n_blocs
    curtes = total_dades // n_blocs
    n_llargs = total_dades % n_blocs
    mides = [curtes] * (n_blocs - n_llargs) + [curtes + 1] * n_llargs

    blocs = [[] for _ in range(n_blocs)]
    index = 0
    for i in range(max(mides)):
        for b, mida in enumerate(mides):
            if i < mida:
                blocs[b].append(paraules[index])
                index += 1
    correccions = [[] for _ in range(n_blocs)]
    for _ in range(n_correccio):
        for b in range(n_blocs):
            correccions[b].append(paraules[index])
            index += 1

    for b in range(n_blocs):
        s = sindromes(blocs[b] + correccions[b], n_correccio)
        if any(s):
            raise AssertionError(f'el bloc {b} no verifica Reed-Solomon: {s}')

    # 5. Descodifiquem el contingut.
    contingut = ''.join(format(p, '08b') for bloc in blocs for p in bloc)
    if contingut[:4] != '0100':
        raise AssertionError('el mode llegit no és byte')
    longitud = int(contingut[4:12], 2)
    octets = bytes(int(contingut[12 + i * 8:20 + i * 8], 2) for i in range(longitud))
    return octets.decode('utf-8')


# ═══════════════════════════════════════════════════════════════════════════
#  Sortida en PNG i SVG
# ═══════════════════════════════════════════════════════════════════════════

def desa_png(moduls: list[list[int]], ruta: Path, escala: int = 20,
             marge: int = 4, fosc=(74, 25, 66), clar=(255, 255, 255)) -> None:
    from PIL import Image

    n = len(moduls)
    costat = (n + marge * 2) * escala
    imatge = Image.new('RGB', (costat, costat), clar)
    pixels = imatge.load()
    for f in range(n):
        for c in range(n):
            if not moduls[f][c]:
                continue
            x0, y0 = (c + marge) * escala, (f + marge) * escala
            for x in range(x0, x0 + escala):
                for y in range(y0, y0 + escala):
                    pixels[x, y] = fosc
    imatge.save(ruta, optimize=True)


def desa_svg(moduls: list[list[int]], ruta: Path, marge: int = 4,
             fosc: str = '#4a1942') -> None:
    n = len(moduls)
    costat = n + marge * 2
    camins = []
    for f in range(n):
        c = 0
        while c < n:
            if moduls[f][c]:
                inici = c
                while c < n and moduls[f][c]:
                    c += 1
                camins.append(f'M{inici + marge} {f + marge}h{c - inici}v1h-{c - inici}z')
            else:
                c += 1
    ruta.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {costat} {costat}" '
        f'shape-rendering="crispEdges" role="img" '
        f'aria-label="Codi QR de l\'enquesta">\n'
        f'  <rect width="{costat}" height="{costat}" fill="#ffffff"/>\n'
        f'  <path fill="{fosc}" d="{"".join(camins)}"/>\n'
        f'</svg>\n',
        encoding='utf-8'
    )


# ═══════════════════════════════════════════════════════════════════════════

def main() -> int:
    text = sys.argv[1] if len(sys.argv) > 1 else 'https://musicaolerdola.cat/enquesta'
    base = Path(sys.argv[2]) if len(sys.argv) > 2 \
        else Path(__file__).resolve().parent.parent / 'assets' / 'img' / 'qr-enquesta'
    base.parent.mkdir(parents=True, exist_ok=True)

    moduls, versio, nivell, patro = genera(text)

    llegit = llegeix(moduls)
    if llegit != text:
        print(f'ERROR de verificació: s\'ha llegit «{llegit}»', file=sys.stderr)
        return 1

    desa_png(moduls, base.with_suffix('.png'))
    desa_svg(moduls, base.with_suffix('.svg'))

    print(f'Text          : {text}')
    print(f'Versió QR     : {versio} ({len(moduls)}x{len(moduls)} mòduls)')
    print(f'Correcció     : nivell {nivell}')
    print(f'Màscara       : {patro}')
    print(f'Verificació   : OK — rellegit i síndromes de Reed-Solomon a zero')
    print(f'Fitxers       : {base.with_suffix(".png")}')
    print(f'                {base.with_suffix(".svg")}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
