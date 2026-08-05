# musicaolerdola.cat

Web de l'**Associació Amics de la Música d'Olèrdola** i enquesta de participació.

- **Producció:** https://musicaolerdola.cat
- **Servidor:** AWS EC2 `ubuntu@13.63.16.49` (`i-xr.duckdns.org`), nginx + PHP 8.3-FPM
- **Versió actual:** v1.1.1

---

## Índex

1. [Què hi ha](#què-hi-ha)
2. [Adreces](#adreces)
3. [Configurar el correu](#configurar-el-correu-important)
4. [Veure els resultats de l'enquesta](#veure-els-resultats-de-lenquesta)
5. [Canviar les preguntes](#canviar-les-preguntes)
6. [El QR i el cartell](#el-qr-i-el-cartell)
7. [El bàner «En construcció»](#el-bàner-en-construcció)
8. [Desplegar](#desplegar)
9. [Seguretat i dades](#seguretat-i-dades)
10. [Estructura de fitxers](#estructura-de-fitxers)

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

## El bàner «En construcció»

La banda diagonal que travessa la portada és un **GIF animat**, generat també
amb una eina pròpia:

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

**Per treure el bàner** quan el web es consideri publicat, esborra el bloc
`<div class="wip-banner">` d'`index.html`.

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
- [ ] Treure el bàner «En construcció» quan el web es consideri publicat
      (esborrar el `<div class="wip-banner">` d'`index.html`).

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
