#!/usr/bin/env bash
#
# Desplegament de musicaolerdola.cat al servidor de producció.
#
#   ./desplegament/desplega.sh
#
# Sincronitza el repositori amb /var/www/html/musicaolerdola i deixa intactes
# les coses que NO viuen a git: api/vendor (dependències de composer) i el
# directori privat amb la configuració i les dades.
#
# Deliberadament NO fa servir --delete: així cap fitxer del servidor
# desapareix per sorpresa. Si cal esborrar-ne algun, fes-ho a mà.

set -euo pipefail

SERVIDOR="ubuntu@13.63.16.49"
CLAU="$HOME/AWS/claus/la-meva-clau-ubuntu.pem"
DESTI="/var/www/html/musicaolerdola/"
ORIGEN="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/"

if [[ ! -f "$CLAU" ]]; then
  echo "No trobo la clau SSH a $CLAU" >&2
  exit 1
fi

# El directori api/ del servidor va quedar amb propietari root quan s'hi va
# instal·lar composer a mà; sense això rsync no hi pot escriure.
echo "▸ Preparant permisos al servidor"
ssh -i "$CLAU" "$SERVIDOR" \
  "sudo mkdir -p $DESTI && sudo chown -R ubuntu:ubuntu $DESTI"

echo "▸ Sincronitzant $ORIGEN → $SERVIDOR:$DESTI"

rsync -avz --human-readable \
  --exclude='.git/' \
  --exclude='.gitignore' \
  --exclude='api/vendor/' \
  --exclude='api/config.php' \
  --exclude='api/config.local.php' \
  --exclude='/dades/' \
  --exclude='*.jsonl' \
  --exclude='__pycache__/' \
  -e "ssh -i $CLAU" \
  "$ORIGEN" "$SERVIDOR:$DESTI"

echo "▸ Comprovant permisos i dependències al servidor"

ssh -i "$CLAU" "$SERVIDOR" bash -s <<'REMOT'
set -euo pipefail
WEB=/var/www/html/musicaolerdola
PRIVAT=/var/www/musicaolerdola-privat

# Les dependències de composer no viatgen per git.
if [[ ! -f "$WEB/api/vendor/autoload.php" ]]; then
  echo "  · instal·lant dependències de composer"
  cd "$WEB/api" && sudo composer install --no-dev --quiet
fi

# El directori privat ha d'existir i ser només per a www-data.
sudo mkdir -p "$PRIVAT/dades"
sudo chown -R www-data:www-data "$PRIVAT"
sudo chmod 750 "$PRIVAT" "$PRIVAT/dades"
[[ -f "$PRIVAT/config.php" ]] && sudo chmod 640 "$PRIVAT/config.php"

if [[ ! -f "$PRIVAT/config.php" ]]; then
  echo "  ⚠ FALTA $PRIVAT/config.php — el correu no funcionarà."
  echo "    Copia-hi api/config.example.php i omple les dades."
fi

sudo chown -R ubuntu:ubuntu "$WEB"
sudo find "$WEB" -type d -exec chmod 755 {} \;
sudo find "$WEB" -type f -exec chmod 644 {} \;
sudo chmod -R go-rwx "$WEB/desplegament" 2>/dev/null || true

echo "  · nginx:"
sudo nginx -t 2>&1 | sed 's/^/    /'
REMOT

echo "▸ Verificant les adreces públiques"
for ruta in / /enquesta /privacitat /cartell /assets/dades/preguntes.json; do
  codi=$(curl -s -o /dev/null -w '%{http_code}' "https://musicaolerdola.cat$ruta")
  printf '  %-34s → %s\n' "$ruta" "$codi"
done

echo "▸ Comprovant que les zones privades estan tancades"
for ruta in /api/lib/bootstrap.php /api/config.example.php /eines/genera-qr.py; do
  codi=$(curl -s -o /dev/null -w '%{http_code}' "https://musicaolerdola.cat$ruta")
  printf '  %-34s → %s (ha de ser 403)\n' "$ruta" "$codi"
done

echo "▸ Fet."
