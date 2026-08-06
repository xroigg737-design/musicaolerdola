# musicaolerdola.cat

Web de l'**Associació Amics de la Música d'Olèrdola** i enquesta de participació.

- **Producció:** https://musicaolerdola.cat
- **Servidor:** AWS EC2 `ubuntu@13.63.16.49` (`i-xr.duckdns.org`), nginx + PHP 8.3-FPM
- **Versió actual:** v1.1.4

---

## Índex

1. [Què hi ha](#què-hi-ha)
2. [Adreces](#adreces)
3. [Configurar el correu](#configurar-el-correu-important)
4. [Veure els resultats de l'enquesta](#veure-els-resultats-de-lenquesta)
5. [Canviar les preguntes](#canviar-les-preguntes)
6. [El QR i el cartell](#el-qr-i-el-cartell)
7. [La imatge de la portada](#la-imatge-de-la-portada)
8. [El bàner «En construcció»](#el-bàner-en-construcció)
9. [Desplegar](#desplegar)
10. [Seguretat i dades](#seguretat-i-dades)
11. [Estructura de fitxers](#estructura-de-fitxers)

---

## Què hi ha

Una web d'una sola pàgina (`index.html`) més una **enquesta de participació**
digital que substitueix l'enquesta en paper. La gent hi arriba escanejant un QR
d'un cartell, contesta en 2 minuts des del mòbil i, si vol, deixa les seves dades
per fer-se sòcia o col·laborar.

Les respostes es desen al servidor i es consulten en un panell propi. No hi ha
cap servei extern pel mig: ni Google Forms, ni analítiques, ni galetes de
seguiment.

## Adreces

| Adreça | Què és |
|---|---|
| `/` | Web principal |
| `/enquesta` | L'enquesta (6 passos) |
| `/privacitat` | Política de privacitat (RGPD) |
| `/cartell` | Cartell A4 imprimible amb el QR |
| `/resultats` | **Panell de resultats** (demana contrasenya) |

---

## Configurar el correu (IMPORTANT)

### Per què no funcionava

El formulari de contacte feia servir l'SMTP d'Outlook amb la contrasenya del
compte. Microsoft ha desactivat l'autenticació bàsica i ara el servidor respon:

```
535 5.7.139 Authentication unsuccessful,
SmtpClientAuthentication is disabled for the Mailbox
```

Només accepta `XOAUTH2` (OAuth2), que per a un web estàtic és desproporcionat.
**La solució és fer servir un altre proveïdor SMTP per enviar.** El correu de
l'associació segueix sent `musicaolerdola@outlook.com`: allà és on arriben els
avisos, només canvia qui els envia.

### Com es configura

Les credencials **no són a git**. Viuen en un únic fitxer al servidor:

```
/var/www/musicaolerdola-privat/config.php
```

Primera instal·lació:

```bash
sudo mkdir -p /var/www/musicaolerdola-privat/dades
sudo cp /var/www/html/musicaolerdola/api/config.example.php \
        /var/www/musicaolerdola-privat/config.php
sudo nano /var/www/musicaolerdola-privat/config.php
sudo chown -R www-data:www-data /var/www/musicaolerdola-privat
sudo chmod 750 /var/www/musicaolerdola-privat /var/www/musicaolerdola-privat/dades
sudo chmod 640 /var/www/musicaolerdola-privat/config.php
```

#### Opció A — Gmail amb contrasenya d'aplicació (la més ràpida)

1. El compte de Gmail ha de tenir la **verificació en dos passos** activada.
2. Anar a https://myaccount.google.com/apppasswords
3. Crear una contrasenya d'aplicació («web musicaolerdola»).
4. Copiar els 16 caràcters (sense espais) al `config.php`:

```php
'smtp' => [
    'host'        => 'smtp.gmail.com',
    'port'        => 587,
    'seguretat'   => 'tls',
    'usuari'      => 'elmeucompte@gmail.com',
    'contrasenya' => 'xxxxxxxxxxxxxxxx',
    'remitent'    => 'elmeucompte@gmail.com',   // el mateix compte
],
```

#### Opció B — Brevo (no depèn de cap compte personal)

300 correus/dia gratis i registre d'enviaments. Crear compte a
https://www.brevo.com → *SMTP & API* → *SMTP*:

```php
'smtp' => [
    'host'        => 'smtp-relay.brevo.com',
    'port'        => 587,
    'seguretat'   => 'tls',
    'usuari'      => '9xxxxx@smtp-brevo.com',
    'contrasenya' => 'xsmtpsib-...',
    'remitent'    => 'musicaolerdola@outlook.com',  // verificat a Brevo
],
```

### Comprovar-ho

```bash
ssh -i ~/AWS/claus/la-meva-clau-ubuntu.pem ubuntu@13.63.16.49
cd /var/www/html/musicaolerdola
sudo -u www-data php eines/prova-correu.php
```

Mostra el diàleg sencer amb el servidor SMTP i, si falla, què significa cada
error. **El primer correu pot anar a la carpeta de brossa**: marca'l com a
correu desitjat.

> **Res es perd si el correu falla.** Tant les respostes de l'enquesta com els
> missatges de contacte es desen al disc *abans* d'intentar enviar l'avís.

---

## Veure els resultats de l'enquesta

https://musicaolerdola.cat/resultats

Per posar-hi contrasenya (o canviar-la), genera el resum al servidor i copia'l
a `admin_hash` del `config.php`:

```bash
php -r 'echo password_hash("LA-TEVA-CONTRASENYA", PASSWORD_DEFAULT), PHP_EOL;'
```

El panell mostra:

- Nombre de respostes i quantes persones volen col·laborar
- Un gràfic de barres per pregunta, amb recompte i percentatge
- Tots els comentaris lliures, amb la data
- La taula de contactes (nom, telèfon, correu, en què volen ajudar)
- **Descàrrega en CSV** llest per obrir amb l'Excel (amb BOM, els accents surten bé)

---

## Canviar les preguntes

Tot està en un únic fitxer:

```
assets/dades/preguntes.json
```

El fan servir alhora el formulari (JavaScript), la validació del servidor (PHP)
i el panell de resultats. Si hi afegeixes una pregunta, apareix als tres llocs
sense tocar res més.

Cada pregunta té:

| Camp | Significat |
|---|---|
| `id` | Identificador intern (`q1`, `q2`…). **No el canviïs** si ja hi ha respostes desades |
| `num` | Número que es mostra |
| `icona` | Emoji decoratiu |
| `text` | L'enunciat |
| `tipus` | `multiple` (caselles), `unica` (una sola opció) o `text` (camp lliure) |
| `opcions` | Llista d'opcions |
| `comentari` | Etiqueta del camp de comentari, o `null` si no en vol |

Les preguntes s'agrupen en `passos`; cada pas és una pantalla de l'assistent.

> **Decisió a revisar:** al full de paper deia «marca totes les opcions», però
> les preguntes 10 (*us faríeu socis?*), 11 (*quota*) i 12 (*preu de l'entrada*)
> estan configurades com a **resposta única**, perquè una sola xifra és molt més
> útil per decidir. Si les vols de resposta múltiple, canvia `"tipus": "unica"`
> per `"tipus": "multiple"`.

---

## El QR i el cartell

El codi QR es genera amb una eina pròpia, **sense cap llibreria externa**:

```bash
python3 eines/genera-qr.py
# o amb un altre text/destí:
python3 eines/genera-qr.py "https://musicaolerdola.cat/enquesta" sortida
```

Crea `assets/img/qr-enquesta.png` i `.svg`. El programa es verifica a si mateix:
torna a llegir la matriu com faria un lector, comprova que els síndromes de
Reed-Solomon són zero i que les dues còpies de la informació de format
coincideixen.

El cartell imprimible és `/cartell` (A4, es pot imprimir 2 per full per tenir-lo
en A5). Obre'l al navegador i prem «Imprimir».

Si algun dia canvies l'adreça de l'enquesta, **regenera el QR** i torna a
imprimir els cartells.

---

## La imatge de la portada

El fons del hero es prepara amb una eina, a partir de l'original quadrat:

```bash
python3 eines/genera-hero.py                      # busca ~/Downloads/olerdola/Best.jpeg
python3 eines/genera-hero.py ruta/a/la/nova.jpg   # o li passes una altra
```

Genera dos retalls, perquè l'original és quadrat i el hero no, i de cada retall
en desa dos fitxers: el WebP, que és el que acaba servint el navegador, i el
JPEG de recanvi.

| Fitxer | Format | Quan es fa servir |
|---|---|---|
| `hero-olerdola.webp` / `.jpg` | 16:9, 1920×1080, 368 / 513 KB | Pantalles amples |
| `hero-olerdola-mobil.webp` / `.jpg` | 3:4, 1080×1440, 262 / 371 KB | Mòbils en vertical |

Els retalls estan triats a mà i escrits a la taula `RETALLS` de l'eina: el
panoràmic talla al 35 % d'alçada (deixa el campanar sencer sense menjar-se el
teclat del piano) i el vertical al 40 % d'amplada (manté el violoncel i la
glicina). El CSS tria l'un o l'altre amb una consulta de mitjans a `.hero-bg`, i
dins de cada regla tria WebP o JPEG amb `image-set()`. El `<head>` de
`index.html` en fa un `preload` amb el mateix `media`, perquè la foto no s'hagi
d'esperar que arribi el full d'estils.

**Per canviar la imatge**, passa la nova a l'eina i torna a desplegar. Si canvia
la composició, potser caldrà retocar els dos percentatges de `RETALLS`.

### La brillantor de la portada

El realçat es fa en dos llocs, i el que convé tocar és el segon:

- **A l'eina** (`ENFOCAMENT`, `CONTRAST`, `SATURACIO`): enfoca el fullatge que
  es perd en reduir la foto i li dona una mica de cos. Canviar-ho vol dir
  tornar a generar els fitxers, o sigui que es deixa suau.
- **Al CSS**, que és on s'ajusta de veritat: `.hero-bg` porta
  `filter: brightness(1.06) contrast(1.08) saturate(1.16)` i `.hero::after` posa
  els vels només a dalt (per llegir-hi el menú) i a baix (per al «Descobreix» i
  per lligar amb la secció morada). Fins a la v1.1.3 hi havia un
  `brightness(0.8)` i un vel negre a tota l'alçada: era el que feia que la
  portada es veiés apagada.

El color de fons de `.hero` és el degradat cel-posta que es veu mentre la foto
encara no ha carregat.

> L'original de 2048×2048 no és al repositori (pesa 3,2 MB i no cal per servir
> el web). **Guarda'l en un lloc segur** si el vols poder reenquadrar.

---

## El bàner «En construcció»

> **Ara mateix està retirat**: el web ja no el mostra. Tot (el GIF, els estils i
> el generador) es conserva per si algun dia el vols tornar a posar.

**Per tornar-lo a posar**, afegeix aquest bloc a `index.html`, just abans de
`<section class="hero" id="inici">`:

```html
<div class="wip-banner" role="img" aria-label="Web en construcció">
  <div class="wip-banner-inner">
    <img class="wip-gif" src="assets/img/en-construccio.gif" alt="En construcció">
    <img class="wip-fix" src="assets/img/en-construccio.png" alt="En construcció">
  </div>
</div>
```

Els estils ja hi són a `assets/css/style.css` (`.wip-banner`), no cal tocar-los.

La banda diagonal és un **GIF animat**, generat amb una eina pròpia:

```bash
python3 eines/genera-gif-construccio.py
```

Crea `assets/img/en-construccio.gif` (63 KB, 12 fotogrames, bucle perfecte:
les franges es desplacen exactament un període) i `en-construccio.png`, la
versió fixa que es mostra a qui té activada la **reducció de moviment** al
sistema operatiu.

Per canviar-ne el text o els colors, edita les constants de dalt del fitxer i
torna a executar-lo. El programa es verifica a si mateix: com que el GIF fa
servir `disposal=1` (cada fotograma només desa el tros que canvia, i això
gairebé li redueix el pes a la meitat), en acabar torna a llegir el fitxer i
comprova que els 12 fotogrames es recomponen exactament.

---

## Desplegar

```bash
./desplegament/desplega.sh
```

Sincronitza el repositori amb `/var/www/html/musicaolerdola`, instal·la les
dependències de composer si falten, arregla els permisos, comprova la
configuració d'nginx i verifica que les adreces públiques responen i que les
privades estan tancades.

**No fa servir `--delete`**: cap fitxer del servidor desapareix sol. Queden fora
de la sincronització `api/vendor/`, la configuració privada i les dades.

La configuració d'nginx està versionada a
`desplegament/nginx-musicaolerdola.cat.conf`. Per instal·lar-la:

```bash
sudo cp desplegament/nginx-musicaolerdola.cat.conf \
        /etc/nginx/sites-available/musicaolerdola.cat
sudo nginx -t && sudo systemctl reload nginx
```

**Recorda incrementar la versió** (peu de `index.html` i capçalera d'aquest
README) a cada desplegament.

---

## Seguretat i dades

- Les credencials SMTP i la contrasenya del panell són **fora del webroot i
  fora de git**, en un fitxer `640` que només pot llegir `www-data`.
- nginx només executa PHP dins de `/api/`, i té bloquejats `/api/lib/`,
  `/api/vendor/`, `/eines/` i `/desplegament/`.
- Les respostes es desen a `/var/www/musicaolerdola-privat/dades/` (fora del
  webroot) en format JSONL: una línia JSON per resposta, amb bloqueig de fitxer
  en escriure. Si una línia es corromp, la resta se salven.
- **No es guarda l'adreça IP.** Se'n desa un resum irreversible (SHA-256 amb
  sal) només per limitar l'spam.
- Contra els robots: camp trampa invisible, temps mínim d'ompliment i màxim 5
  enviaments per hora i dispositiu.
- El bloc de dades personals de l'enquesta és opcional i exigeix marcar el
  consentiment; si no es marca, el servidor rebutja les dades.

### Còpia de seguretat de les respostes

Les dades **no són a git** (són dades personals). Per baixar-te'n una còpia:

```bash
scp -i ~/AWS/claus/la-meva-clau-ubuntu.pem \
    ubuntu@13.63.16.49:/tmp/respostes.jsonl .
# abans, al servidor:
sudo cp /var/www/musicaolerdola-privat/dades/respostes.jsonl /tmp/ && sudo chmod 644 /tmp/respostes.jsonl
```

O més senzill: entra a `/resultats` i prem **Descarrega CSV**.

### Pendents

- [ ] **Canviar la contrasenya del compte `musicaolerdola@outlook.com`**: estava
      en text pla dins `api/send-mail.php` al servidor.
- [ ] Afegir el **NIF i el domicili social** de l'associació a `privacitat.html`
      (apartat «Qui és el responsable») quan estigui constituïda.
- [ ] Enllaçar els perfils reals d'Instagram i Facebook a `index.html`
      (ara apunten a `#`).
- [ ] Omplir les xifres de la secció «L'Associació» (concerts, socis, anys), que
      ara mostren símbols.
- [x] Treure el bàner «En construcció» — fet a la v1.1.2.

---

## Estructura de fitxers

```
index.html                      Web principal
enquesta.html                   L'enquesta (l'esquelet; les preguntes venen del JSON)
privacitat.html                 Política de privacitat
cartell.html                    Cartell A4 imprimible amb el QR
manifest.json                   Metadades per instal·lar-la com a aplicació

assets/
  css/style.css                 Estils del web
  css/enquesta.css              Estils de l'enquesta i de la privacitat
  js/main.js                    Menú, animacions i formulari de contacte
  js/enquesta.js                Assistent de l'enquesta
  dades/preguntes.json          ← LES PREGUNTES (font única)
  img/                          Logotips, hero, icones, el QR i el GIF del bàner

api/
  send-mail.php                 Formulari de contacte
  enquesta.php                  Recepció de respostes de l'enquesta
  admin.php                     Panell de resultats (= /resultats)
  config.example.php            Plantilla de configuració (sense secrets)
  lib/bootstrap.php             Configuració, sanejat, anti-spam, desat
  lib/mailer.php                Enviament de correu
  lib/preguntes.php             Lectura de preguntes.json
  composer.json / .lock         Dependència: PHPMailer
  vendor/                       (no és a git: `composer install`)

eines/
  genera-qr.py                  Generador de QR propi, amb autoverificació
  genera-gif-construccio.py     GIF animat del bàner «En construcció»
  genera-hero.py                Retalla i optimitza la imatge de la portada
  prova-correu.php              Diagnòstic de l'SMTP

desplegament/
  desplega.sh                   Desplegament a producció
  nginx-musicaolerdola.cat.conf Configuració d'nginx versionada

guia-dns-cdmon.py               Generadors dels PDF de documentació del domini
guia-registre-domini.py
```

Fora del repositori, al servidor:

```
/var/www/musicaolerdola-privat/
  config.php                    Credencials SMTP + contrasenya del panell (640, www-data)
  dades/respostes.jsonl         Respostes de l'enquesta
  dades/missatges.jsonl         Missatges del formulari de contacte
```
