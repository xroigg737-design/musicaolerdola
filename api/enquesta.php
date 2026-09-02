<?php
/**
 * Recepció de les respostes de l'enquesta de participació.
 *
 * Ordre deliberat: primer es GUARDA la resposta i després s'intenta enviar
 * l'avís per correu. Si el correu falla, la resposta ja està desada i mai
 * es perd cap dada.
 */

declare(strict_types=1);

require_once __DIR__ . '/lib/bootstrap.php';
require_once __DIR__ . '/lib/preguntes.php';
require_once __DIR__ . '/lib/mailer.php';

aamo_nomes_post();

// ── Anti-spam ───────────────────────────────────────────────────────────────
// 1) Camp trampa: invisible per a les persones, els robots l'omplen.
if (aamo_text($_POST['web'] ?? '') !== '') {
    aamo_json(['success' => true]); // fingim que ha anat bé
}

// 2) Temps mínim: qui contesta 15 preguntes no ho fa en 5 segons.
$obertura = (int) ($_POST['obertura'] ?? 0);
if ($obertura > 0 && (time() * 1000 - $obertura) < 5000) {
    aamo_error('El formulari s\'ha enviat massa de pressa. Torna-ho a provar.', 429);
}

// 3) Màxim 5 respostes per hora des del mateix lloc.
$visitant = aamo_hash_visitant();
if (!aamo_limit_peticions('enq-' . $visitant, 5, 3600)) {
    aamo_error('Ja hem rebut diverses respostes des d\'aquest dispositiu. Gràcies!', 429);
}

// ── Validació de les respostes ──────────────────────────────────────────────
$respostes  = [];
$te_resposta = false;

foreach (aamo_preguntes() as $pregunta) {
    $id      = (string) $pregunta['id'];
    $tipus   = (string) ($pregunta['tipus'] ?? 'multiple');
    $opcions = array_map('strval', $pregunta['opcions'] ?? []);

    if ($tipus === 'text') {
        $valor = aamo_text_llarg($_POST[$id] ?? '', 3000);
        if ($valor !== '') {
            $te_resposta = true;
        }
        $respostes[$id] = ['valors' => [], 'comentari' => $valor];
        continue;
    }

    $triades = aamo_opcions($_POST[$id] ?? [], $opcions);
    if ($tipus === 'unica' && count($triades) > 1) {
        $triades = [$triades[0]];
    }

    $comentari = aamo_text_llarg($_POST[$id . '_comentari'] ?? '', 1000);

    if ($triades !== [] || $comentari !== '') {
        $te_resposta = true;
    }

    $respostes[$id] = ['valors' => $triades, 'comentari' => $comentari];
}

if (!$te_resposta) {
    aamo_error('L\'enquesta és buida: contesta almenys una pregunta.', 400);
}

// ── Bloc de col·laboració i dades de contacte (opcional) ────────────────────
$def_collab      = aamo_definicio_enquesta()['collaboracio'] ?? ['opcions' => []];
$opcions_collab  = array_map('strval', $def_collab['opcions'] ?? []);
$collaboracio    = aamo_opcions($_POST['collaboracio'] ?? [], $opcions_collab);
$collab_altres   = aamo_text($_POST['collaboracio_altres'] ?? '', 300);

$nom      = aamo_text($_POST['nom'] ?? '', 120);
$telefon  = aamo_text($_POST['telefon'] ?? '', 40);
$email    = aamo_text($_POST['email'] ?? '', 180);
$consent  = !empty($_POST['consentiment']);

$vol_contacte = ($nom !== '' || $telefon !== '' || $email !== '' || $collaboracio !== []);

if ($vol_contacte) {
    if (!$consent) {
        aamo_error('Per deixar-nos les teves dades cal acceptar la política de privacitat.', 400);
    }
    if ($nom === '') {
        aamo_error('Cal indicar el nom i els cognoms.', 400);
    }
    if ($email === '' && $telefon === '') {
        aamo_error('Deixa\'ns almenys un correu electrònic o un telèfon per poder-te contactar.', 400);
    }
    if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        aamo_error('El correu electrònic no és vàlid.', 400);
    }
}

// ── Desem la resposta ───────────────────────────────────────────────────────
$registre = [
    'data'         => date('c'),
    'versio'       => aamo_definicio_enquesta()['versio'] ?? 1,
    'respostes'    => $respostes,
    'collaboracio' => $collaboracio,
    'collab_altres'=> $collab_altres,
    'contacte'     => $vol_contacte ? [
        'nom'     => $nom,
        'telefon' => $telefon,
        'email'   => $email,
    ] : null,
    'consentiment' => $vol_contacte ? true : false,
    'visitant'     => $visitant, // hash amb sal, no és la IP
];

if (!aamo_desa_registre('respostes.jsonl', $registre)) {
    aamo_error('No hem pogut desar la resposta. Torna-ho a provar en uns minuts.', 500);
}

// ── Avís per correu (si falla, la resposta ja està desada) ──────────────────
$cfg = aamo_config();
$correu_enviat = false;

if (!empty($cfg['avisa_enquesta'])) {
    $files = '';
    foreach (aamo_preguntes() as $pregunta) {
        $r = $respostes[(string) $pregunta['id']];
        if ($r['valors'] === [] && $r['comentari'] === '') {
            continue;
        }
        $etiqueta = htmlspecialchars(
            $pregunta['num'] . '. ' . $pregunta['text'],
            ENT_QUOTES,
            'UTF-8'
        );
        $valor = htmlspecialchars(implode(' · ', $r['valors']), ENT_QUOTES, 'UTF-8');
        if ($r['comentari'] !== '') {
            $com = nl2br(htmlspecialchars($r['comentari'], ENT_QUOTES, 'UTF-8'));
            $valor .= ($valor !== '' ? '<br>' : '')
                . '<em style="color:#6b5a6b;">' . $com . '</em>';
        }
        $files .= '<tr>'
            . '<td style="padding:8px 12px 8px 0;vertical-align:top;border-bottom:1px solid #eee;font-weight:bold;width:45%;">'
            . $etiqueta . '</td>'
            . '<td style="padding:8px 0;vertical-align:top;border-bottom:1px solid #eee;">'
            . ($valor !== '' ? $valor : '—') . '</td>'
            . '</tr>';
    }

    $bloc_contacte = '';
    if ($vol_contacte) {
        $llista = htmlspecialchars(implode(' · ', $collaboracio), ENT_QUOTES, 'UTF-8');
        if ($collab_altres !== '') {
            $llista .= ($llista !== '' ? ' · ' : '')
                . htmlspecialchars($collab_altres, ENT_QUOTES, 'UTF-8');
        }
        $bloc_contacte = '<div style="margin-top:24px;padding:16px;background:#faf8f4;border-left:4px solid #c8a84e;">'
            . '<h2 style="margin:0 0 10px;font-size:16px;color:#4a1942;">Vol col·laborar amb l\'Associació</h2>'
            . '<p style="margin:0 0 8px;"><strong>Com:</strong> ' . ($llista !== '' ? $llista : '—') . '</p>'
            . '<p style="margin:0;"><strong>Nom:</strong> ' . htmlspecialchars($nom, ENT_QUOTES, 'UTF-8') . '<br>'
            . '<strong>Telèfon:</strong> ' . htmlspecialchars($telefon !== '' ? $telefon : '—', ENT_QUOTES, 'UTF-8') . '<br>'
            . '<strong>Correu:</strong> ' . htmlspecialchars($email !== '' ? $email : '—', ENT_QUOTES, 'UTF-8') . '</p>'
            . '</div>';
    }

    $html = aamo_plantilla_correu(
        'Nova resposta a l\'enquesta',
        '<table style="border-collapse:collapse;width:100%;font-size:14px;">' . $files . '</table>' . $bloc_contacte
    );

    $text = "Nova resposta a l'enquesta de participació\n\n";
    foreach (aamo_preguntes() as $pregunta) {
        $r = $respostes[(string) $pregunta['id']];
        if ($r['valors'] === [] && $r['comentari'] === '') {
            continue;
        }
        $text .= $pregunta['num'] . '. ' . $pregunta['text'] . "\n";
        if ($r['valors'] !== []) {
            $text .= '   ' . implode(' · ', $r['valors']) . "\n";
        }
        if ($r['comentari'] !== '') {
            $text .= '   Comentari: ' . $r['comentari'] . "\n";
        }
    }
    if ($vol_contacte) {
        $text .= "\n--- Vol col·laborar ---\n"
            . 'Com: ' . implode(' · ', $collaboracio) . ($collab_altres !== '' ? ' · ' . $collab_altres : '') . "\n"
            . "Nom: $nom\nTelèfon: $telefon\nCorreu: $email\n";
    }

    $assumpte = $vol_contacte
        ? "Enquesta + contacte: $nom"
        : 'Nova resposta a l\'enquesta';

    $correu_enviat = aamo_envia_correu(
        $assumpte,
        $html,
        $text,
        ($vol_contacte && $email !== '') ? [$email, $nom] : null
    );
}

aamo_json([
    'success' => true,
    'avis'    => $correu_enviat, // informatiu: la resposta es desa igualment
]);
