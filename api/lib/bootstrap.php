<?php
/**
 * Bootstrap comú per a tots els endpoints de l'API.
 *
 * Carrega la configuració (que viu FORA del webroot i FORA de git),
 * i ofereix funcions d'utilitat: respostes JSON, sanejat i límit de peticions.
 */

declare(strict_types=1);

// ── Càrrega de la configuració ──────────────────────────────────────────────
// Ordre de cerca:
//   1. Variable d'entorn MUSICAOLERDOLA_CONFIG (per si es vol moure)
//   2. /var/www/musicaolerdola-privat/config.php  ← producció
//   3. api/config.local.php                       ← desenvolupament (gitignorat)
function aamo_config(): array
{
    static $config = null;
    if ($config !== null) {
        return $config;
    }

    $candidats = array_filter([
        getenv('MUSICAOLERDOLA_CONFIG') ?: null,
        '/var/www/musicaolerdola-privat/config.php',
        __DIR__ . '/../config.local.php',
    ]);

    foreach ($candidats as $ruta) {
        if (is_readable($ruta)) {
            $carregat = require $ruta;
            if (is_array($carregat)) {
                $config = $carregat + aamo_config_per_defecte();
                return $config;
            }
        }
    }

    // Sense fitxer de configuració seguim funcionant: les dades es guarden
    // igualment i només es perd la notificació per correu.
    error_log('AAMO: no s\'ha trobat cap fitxer de configuració.');
    $config = aamo_config_per_defecte();
    return $config;
}

function aamo_config_per_defecte(): array
{
    return [
        'smtp'            => [],
        'desti_avisos'    => 'musicaolerdola@outlook.com',
        'dir_dades'       => '/var/www/musicaolerdola-privat/dades',
        'admin_hash'      => '',
        'avisa_enquesta'  => true,
        'origen_permes'   => 'https://musicaolerdola.cat',
    ];
}

// ── Respostes JSON ──────────────────────────────────────────────────────────
function aamo_json(array $dades, int $codi = 200): never
{
    http_response_code($codi);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($dades, JSON_UNESCAPED_UNICODE);
    exit;
}

function aamo_error(string $missatge, int $codi = 400): never
{
    aamo_json(['error' => $missatge], $codi);
}

// ── Capçaleres i mètode ─────────────────────────────────────────────────────
function aamo_nomes_post(): void
{
    $cfg = aamo_config();
    header('Access-Control-Allow-Origin: ' . $cfg['origen_permes']);
    header('Access-Control-Allow-Methods: POST');
    header('Access-Control-Allow-Headers: Content-Type');
    header('X-Content-Type-Options: nosniff');

    if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') {
        http_response_code(204);
        exit;
    }
    if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
        aamo_error('Mètode no permès', 405);
    }
}

// ── Sanejat ─────────────────────────────────────────────────────────────────
/** Text d'una línia: sense caràcters de control, retallat i amb llargada màxima. */
function aamo_text(mixed $valor, int $max = 500): string
{
    if (!is_string($valor)) {
        return '';
    }
    $valor = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $valor) ?? '';
    return mb_substr(trim($valor), 0, $max);
}

/** Text multilínia: conserva els salts de línia. */
function aamo_text_llarg(mixed $valor, int $max = 3000): string
{
    if (!is_string($valor)) {
        return '';
    }
    $valor = str_replace(["\r\n", "\r"], "\n", $valor);
    $valor = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $valor) ?? '';
    return mb_substr(trim($valor), 0, $max);
}

/**
 * Llista de valors, validada contra les opcions permeses.
 * Descarta qualsevol cosa que no sigui una opció coneguda.
 */
function aamo_opcions(mixed $valor, array $permeses): array
{
    if (is_string($valor)) {
        $valor = [$valor];
    }
    if (!is_array($valor)) {
        return [];
    }
    $net = [];
    foreach ($valor as $v) {
        if (is_string($v) && in_array($v, $permeses, true) && !in_array($v, $net, true)) {
            $net[] = $v;
        }
    }
    return $net;
}

// ── Identificació anònima del visitant (per limitar l'spam) ─────────────────
// No guardem la IP: només un hash amb sal, que serveix per comptar peticions
// i no permet recuperar l'adreça original. Minimització de dades (RGPD).
function aamo_hash_visitant(): string
{
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'desconeguda';
    return substr(hash('sha256', 'aamo|' . $ip), 0, 16);
}

/**
 * Límit de peticions per visitant.
 * Retorna false si ha superat $max peticions en $finestra segons.
 */
function aamo_limit_peticions(string $clau, int $max, int $finestra): bool
{
    $dir = sys_get_temp_dir() . '/aamo-limits';
    if (!is_dir($dir) && !@mkdir($dir, 0700, true) && !is_dir($dir)) {
        return true; // si no podem controlar-ho, no bloquegem ningú
    }

    $fitxer = $dir . '/' . preg_replace('/[^a-z0-9_-]/i', '', $clau) . '.json';
    $ara    = time();
    $marques = [];

    $fp = @fopen($fitxer, 'c+');
    if ($fp === false) {
        return true;
    }

    try {
        if (!flock($fp, LOCK_EX)) {
            return true;
        }
        $contingut = stream_get_contents($fp);
        if (is_string($contingut) && $contingut !== '') {
            $desat = json_decode($contingut, true);
            if (is_array($desat)) {
                $marques = array_values(array_filter(
                    $desat,
                    fn($t) => is_int($t) && $t > $ara - $finestra
                ));
            }
        }

        if (count($marques) >= $max) {
            return false;
        }

        $marques[] = $ara;
        ftruncate($fp, 0);
        rewind($fp);
        fwrite($fp, json_encode($marques));
        fflush($fp);
        return true;
    } finally {
        flock($fp, LOCK_UN);
        fclose($fp);
    }
}

// ── Emmagatzematge ──────────────────────────────────────────────────────────
/**
 * Afegeix un registre al fitxer JSONL indicat, de manera atòmica.
 * Cada línia és un JSON independent: si una es corromp, la resta se salva.
 */
function aamo_desa_registre(string $nom_fitxer, array $registre): bool
{
    $cfg = aamo_config();
    $dir = $cfg['dir_dades'];

    if (!is_dir($dir) && !@mkdir($dir, 0750, true) && !is_dir($dir)) {
        error_log("AAMO: no s'ha pogut crear el directori de dades: $dir");
        return false;
    }

    $ruta  = rtrim($dir, '/') . '/' . basename($nom_fitxer);
    $linia = json_encode($registre, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    if ($linia === false) {
        error_log('AAMO: no s\'ha pogut serialitzar el registre.');
        return false;
    }

    $ok = @file_put_contents($ruta, $linia . "\n", FILE_APPEND | LOCK_EX);
    if ($ok === false) {
        error_log("AAMO: no s'ha pogut escriure a $ruta");
        return false;
    }
    @chmod($ruta, 0640);
    return true;
}

/** Llegeix tots els registres d'un fitxer JSONL. */
function aamo_llegeix_registres(string $nom_fitxer): array
{
    $cfg  = aamo_config();
    $ruta = rtrim($cfg['dir_dades'], '/') . '/' . basename($nom_fitxer);
    if (!is_readable($ruta)) {
        return [];
    }

    $registres = [];
    $fp = fopen($ruta, 'r');
    if ($fp === false) {
        return [];
    }
    while (($linia = fgets($fp)) !== false) {
        $linia = trim($linia);
        if ($linia === '') {
            continue;
        }
        $dades = json_decode($linia, true);
        if (is_array($dades)) {
            $registres[] = $dades;
        }
    }
    fclose($fp);
    return $registres;
}
