<?php
/**
 * Panell de resultats de l'enquesta.
 *
 * Accés protegit amb contrasenya (hash a la configuració privada).
 * URL: https://musicaolerdola.cat/api/admin.php
 */

declare(strict_types=1);

require_once __DIR__ . '/lib/bootstrap.php';
require_once __DIR__ . '/lib/preguntes.php';

$cfg = aamo_config();

// El panell es visita a /resultats, que nginx reescriu cap a /api/admin.php.
// La galeta ha de tenir àmbit '/' o el navegador no la tornaria a enviar mai.
session_set_cookie_params([
    'lifetime' => 0,
    'path'     => '/',
    'secure'   => !empty($_SERVER['HTTPS']),
    'httponly' => true,
    'samesite' => 'Strict',
]);
session_name('AAMOADMIN');
session_start();

$e = fn(?string $t): string => htmlspecialchars((string) $t, ENT_QUOTES, 'UTF-8');

// ── Sortir ──────────────────────────────────────────────────────────────────
if (isset($_GET['surt'])) {
    $_SESSION = [];
    session_destroy();
    header('Location: admin.php');
    exit;
}

// ── Entrar ──────────────────────────────────────────────────────────────────
$error = '';
$hash  = (string) ($cfg['admin_hash'] ?? '');

if (($_SERVER['REQUEST_METHOD'] ?? '') === 'POST' && isset($_POST['contrasenya'])) {
    if (!aamo_limit_peticions('adm-' . aamo_hash_visitant(), 10, 900)) {
        $error = 'Massa intents. Espera un quart d\'hora.';
    } elseif ($hash === '') {
        $error = 'El panell no té cap contrasenya configurada (admin_hash).';
    } elseif (password_verify((string) $_POST['contrasenya'], $hash)) {
        session_regenerate_id(true);
        $_SESSION['aamo_admin'] = true;
    } else {
        $error = 'Contrasenya incorrecta.';
        usleep(500000);
    }
}

$autenticat = !empty($_SESSION['aamo_admin']);

// ── Pantalla d'accés ────────────────────────────────────────────────────────
if (!$autenticat) {
    header('Content-Type: text/html; charset=utf-8');
    header('X-Robots-Tag: noindex, nofollow');
    ?>
<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>Resultats de l'enquesta — AAMO</title>
<style>
  *{box-sizing:border-box}
  body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;
       background:linear-gradient(135deg,#4a1942,#6b2d6b);
       font-family:'Cormorant Garamond',Georgia,serif;color:#2a1a2a}
  .caixa{background:#fffef9;padding:40px;border-radius:10px;max-width:380px;width:100%;
         box-shadow:0 20px 50px rgba(0,0,0,.3)}
  h1{margin:0 0 6px;font-size:1.6rem;color:#4a1942;font-weight:600}
  p.sub{margin:0 0 24px;color:#6b5a6b;font-size:.95rem}
  label{display:block;font-size:.85rem;text-transform:uppercase;letter-spacing:.08em;
        color:#6b5a6b;margin-bottom:8px}
  input{width:100%;padding:12px 14px;border:1px solid rgba(106,45,107,.25);border-radius:6px;
        font-size:1rem;font-family:inherit;background:#faf8f4}
  input:focus{outline:none;border-color:#c8a84e;box-shadow:0 0 0 3px rgba(200,168,78,.2)}
  button{width:100%;margin-top:18px;padding:13px;border:0;border-radius:6px;cursor:pointer;
         background:#6b2d6b;color:#fff;font-family:inherit;font-size:1.05rem;letter-spacing:.03em}
  button:hover{background:#4a1942}
  .err{margin:16px 0 0;padding:10px 12px;background:#fdecea;color:#a5281b;border-radius:6px;
       font-size:.9rem}
</style>
</head>
<body>
  <form class="caixa" method="POST" autocomplete="off">
    <h1>&#9835; Resultats de l'enquesta</h1>
    <p class="sub">Amics de la Música d'Olèrdola</p>
    <label for="c">Contrasenya</label>
    <input type="password" id="c" name="contrasenya" required autofocus>
    <button type="submit">Entrar</button>
    <?php if ($error !== ''): ?><p class="err"><?= $e($error) ?></p><?php endif; ?>
  </form>
</body>
</html>
    <?php
    exit;
}

// ── Dades ───────────────────────────────────────────────────────────────────
$registres = aamo_llegeix_registres('respostes.jsonl');
$preguntes = aamo_preguntes();
$def       = aamo_definicio_enquesta();
$total     = count($registres);

// ── Descàrrega CSV ──────────────────────────────────────────────────────────
if (isset($_GET['csv'])) {
    $nom_fitxer = 'enquesta-aamo-' . date('Y-m-d') . '.csv';
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="' . $nom_fitxer . '"');

    $sortida = fopen('php://output', 'w');
    fwrite($sortida, "\xEF\xBB\xBF"); // BOM: perquè l'Excel llegeixi els accents

    $capcaleres = ['Data'];
    foreach ($preguntes as $p) {
        $capcaleres[] = $p['num'] . '. ' . $p['text'];
        if (($p['tipus'] ?? '') !== 'text') {
            $capcaleres[] = $p['num'] . '. Comentari';
        }
    }
    $capcaleres[] = 'Vol col·laborar com';
    $capcaleres[] = 'Col·laboració (altres)';
    $capcaleres[] = 'Nom';
    $capcaleres[] = 'Telèfon';
    $capcaleres[] = 'Correu';
    fputcsv($sortida, $capcaleres, ';');

    foreach ($registres as $r) {
        $fila = [$r['data'] ?? ''];
        foreach ($preguntes as $p) {
            $resp = $r['respostes'][$p['id']] ?? ['valors' => [], 'comentari' => ''];
            if (($p['tipus'] ?? '') === 'text') {
                $fila[] = (string) ($resp['comentari'] ?? '');
            } else {
                $fila[] = implode(' | ', $resp['valors'] ?? []);
                $fila[] = (string) ($resp['comentari'] ?? '');
            }
        }
        $fila[] = implode(' | ', $r['collaboracio'] ?? []);
        $fila[] = (string) ($r['collab_altres'] ?? '');
        $fila[] = (string) ($r['contacte']['nom'] ?? '');
        $fila[] = (string) ($r['contacte']['telefon'] ?? '');
        $fila[] = (string) ($r['contacte']['email'] ?? '');
        fputcsv($sortida, $fila, ';');
    }
    fclose($sortida);
    exit;
}

// ── Agregació ───────────────────────────────────────────────────────────────
$recompte  = [];   // id pregunta => [opció => vegades]
$comentaris = [];  // id pregunta => [textos]

foreach ($preguntes as $p) {
    $recompte[$p['id']]   = array_fill_keys(array_map('strval', $p['opcions'] ?? []), 0);
    $comentaris[$p['id']] = [];
}

foreach ($registres as $r) {
    foreach ($preguntes as $p) {
        $resp = $r['respostes'][$p['id']] ?? null;
        if (!is_array($resp)) {
            continue;
        }
        foreach ($resp['valors'] ?? [] as $v) {
            if (isset($recompte[$p['id']][$v])) {
                $recompte[$p['id']][$v]++;
            }
        }
        $com = trim((string) ($resp['comentari'] ?? ''));
        if ($com !== '') {
            $comentaris[$p['id']][] = ['text' => $com, 'data' => (string) ($r['data'] ?? '')];
        }
    }
}

$recompte_collab = array_fill_keys(array_map('strval', $def['collaboracio']['opcions'] ?? []), 0);
$contactes = [];
foreach ($registres as $r) {
    foreach ($r['collaboracio'] ?? [] as $v) {
        if (isset($recompte_collab[$v])) {
            $recompte_collab[$v]++;
        }
    }
    if (!empty($r['contacte']['nom'])) {
        $contactes[] = $r;
    }
}

$primera = $total > 0 ? (string) ($registres[0]['data'] ?? '') : '';
$ultima  = $total > 0 ? (string) ($registres[$total - 1]['data'] ?? '') : '';
$data_ct = fn(string $iso): string => $iso === ''
    ? '—'
    : date('d/m/Y H:i', strtotime($iso) ?: time());

header('Content-Type: text/html; charset=utf-8');
header('X-Robots-Tag: noindex, nofollow');
?>
<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>Resultats de l'enquesta — AAMO</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&display=swap" rel="stylesheet">
<style>
  *{box-sizing:border-box}
  body{margin:0;background:#faf8f4;color:#2a1a2a;
       font-family:'Cormorant Garamond',Georgia,serif;font-size:17px;line-height:1.5}
  header{background:linear-gradient(135deg,#4a1942,#6b2d6b);color:#fff;padding:26px 28px}
  header h1{margin:0;font-size:1.7rem;font-weight:600;color:#e8d48b}
  header p{margin:4px 0 0;font-size:.95rem;color:rgba(255,255,255,.75)}
  .accions{margin-top:16px;display:flex;gap:10px;flex-wrap:wrap}
  .btn{display:inline-block;padding:9px 18px;border-radius:6px;text-decoration:none;
       font-size:.95rem;border:1px solid rgba(255,255,255,.35);color:#fff}
  .btn:hover{background:rgba(255,255,255,.12)}
  .btn-or{background:#c8a84e;border-color:#c8a84e;color:#3a1230;font-weight:600}
  .btn-or:hover{background:#e8d48b}
  main{max-width:1000px;margin:0 auto;padding:28px}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:28px}
  .kpi{background:#fffef9;border:1px solid rgba(106,45,107,.12);border-radius:8px;padding:18px 20px}
  .kpi b{display:block;font-size:2.1rem;color:#6b2d6b;line-height:1.1}
  .kpi span{font-size:.85rem;text-transform:uppercase;letter-spacing:.07em;color:#6b5a6b}
  section.q{background:#fffef9;border:1px solid rgba(106,45,107,.12);border-radius:8px;
            padding:20px 22px;margin-bottom:16px}
  section.q h2{margin:0 0 14px;font-size:1.15rem;color:#4a1942;font-weight:600}
  section.q h2 em{font-style:normal;color:#c8a84e;margin-right:6px}
  .barra{margin-bottom:9px}
  .barra .fila{display:flex;justify-content:space-between;gap:12px;font-size:.95rem;margin-bottom:3px}
  .barra .fila span:last-child{color:#6b5a6b;white-space:nowrap;font-variant-numeric:tabular-nums}
  .pista{height:9px;background:rgba(106,45,107,.09);border-radius:5px;overflow:hidden}
  .plena{height:100%;background:linear-gradient(90deg,#6b2d6b,#c8a84e);border-radius:5px}
  .coms{margin-top:14px;padding-top:12px;border-top:1px dashed rgba(106,45,107,.18)}
  .coms h3{margin:0 0 8px;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;color:#6b5a6b}
  .coms li{margin-bottom:7px;color:#3a2a3a}
  .coms ul{margin:0;padding-left:18px}
  table{width:100%;border-collapse:collapse;font-size:.95rem}
  th,td{text-align:left;padding:9px 10px;border-bottom:1px solid rgba(106,45,107,.12);
        vertical-align:top}
  th{font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;color:#6b5a6b}
  .buit{padding:40px;text-align:center;color:#6b5a6b;background:#fffef9;border-radius:8px;
        border:1px dashed rgba(106,45,107,.25)}
  .taula-scroll{overflow-x:auto}
  footer{text-align:center;padding:24px;color:#6b5a6b;font-size:.85rem}
  @media(max-width:600px){main{padding:18px}header{padding:20px}}
</style>
</head>
<body>
<header>
  <h1>&#9835; Resultats de l'enquesta</h1>
  <p>Associació Amics de la Música d'Olèrdola</p>
  <div class="accions">
    <a class="btn btn-or" href="?csv=1">&#11123; Descarrega CSV (Excel)</a>
    <a class="btn" href="/enquesta" target="_blank" rel="noopener">Veure l'enquesta</a>
    <a class="btn" href="?surt=1">Sortir</a>
  </div>
</header>

<main>
  <div class="kpis">
    <div class="kpi"><b><?= $total ?></b><span>Respostes</span></div>
    <div class="kpi"><b><?= count($contactes) ?></b><span>Volen col·laborar</span></div>
    <div class="kpi"><b><?= $e($data_ct($primera)) ?></b><span>Primera resposta</span></div>
    <div class="kpi"><b><?= $e($data_ct($ultima)) ?></b><span>Última resposta</span></div>
  </div>

<?php if ($total === 0): ?>
  <div class="buit">
    <p style="font-size:1.2rem;margin:0 0 6px;">Encara no hi ha cap resposta.</p>
    <p style="margin:0;">Comparteix el QR o l'enllaç <strong>musicaolerdola.cat/enquesta</strong> i aniran apareixent aquí.</p>
  </div>
<?php else: ?>

  <?php foreach ($preguntes as $p): ?>
    <?php
      $id     = (string) $p['id'];
      $dades  = $recompte[$id] ?? [];
      $maxim  = $dades === [] ? 0 : max($dades);
      $es_text = ($p['tipus'] ?? '') === 'text';
    ?>
    <section class="q">
      <h2><em><?= (int) $p['num'] ?>.</em><?= $e($p['text']) ?></h2>

      <?php if (!$es_text): ?>
        <?php
          arsort($dades);
          foreach ($dades as $opcio => $vegades):
            $pct = $total > 0 ? round($vegades / $total * 100) : 0;
            $amplada = $maxim > 0 ? round($vegades / $maxim * 100) : 0;
        ?>
          <div class="barra">
            <div class="fila">
              <span><?= $e((string) $opcio) ?></span>
              <span><?= (int) $vegades ?> · <?= (int) $pct ?>%</span>
            </div>
            <div class="pista"><div class="plena" style="width:<?= (int) $amplada ?>%"></div></div>
          </div>
        <?php endforeach; ?>
      <?php endif; ?>

      <?php if (!empty($comentaris[$id])): ?>
        <div class="coms">
          <h3><?= $es_text ? 'Respostes' : 'Comentaris' ?> (<?= count($comentaris[$id]) ?>)</h3>
          <ul>
            <?php foreach ($comentaris[$id] as $c): ?>
              <li><?= nl2br($e($c['text'])) ?>
                <span style="color:#a08fa0;font-size:.8rem;">— <?= $e($data_ct($c['data'])) ?></span></li>
            <?php endforeach; ?>
          </ul>
        </div>
      <?php elseif ($es_text): ?>
        <p style="margin:0;color:#6b5a6b;">Cap resposta encara.</p>
      <?php endif; ?>
    </section>
  <?php endforeach; ?>

  <section class="q">
    <h2><em>&#10022;</em>Vol col·laborar com a…</h2>
    <?php
      $max_c = $recompte_collab === [] ? 0 : max($recompte_collab);
      arsort($recompte_collab);
      foreach ($recompte_collab as $opcio => $vegades):
        $amplada = $max_c > 0 ? round($vegades / $max_c * 100) : 0;
    ?>
      <div class="barra">
        <div class="fila">
          <span><?= $e((string) $opcio) ?></span>
          <span><?= (int) $vegades ?></span>
        </div>
        <div class="pista"><div class="plena" style="width:<?= (int) $amplada ?>%"></div></div>
      </div>
    <?php endforeach; ?>
  </section>

  <section class="q">
    <h2><em>&#9993;</em>Contactes (<?= count($contactes) ?>)</h2>
    <?php if ($contactes === []): ?>
      <p style="margin:0;color:#6b5a6b;">Encara ningú no ha deixat les seves dades.</p>
    <?php else: ?>
      <div class="taula-scroll">
      <table>
        <thead><tr>
          <th>Data</th><th>Nom</th><th>Telèfon</th><th>Correu</th><th>Vol col·laborar en</th>
        </tr></thead>
        <tbody>
        <?php foreach (array_reverse($contactes) as $c): ?>
          <tr>
            <td><?= $e($data_ct((string) ($c['data'] ?? ''))) ?></td>
            <td><?= $e((string) ($c['contacte']['nom'] ?? '')) ?></td>
            <td><?= $e((string) ($c['contacte']['telefon'] ?? '')) ?></td>
            <td><?php $m = (string) ($c['contacte']['email'] ?? ''); ?>
              <?php if ($m !== ''): ?><a href="mailto:<?= $e($m) ?>"><?= $e($m) ?></a><?php endif; ?></td>
            <td><?= $e(implode(' · ', $c['collaboracio'] ?? [])) ?>
              <?php if (!empty($c['collab_altres'])): ?>
                <em>(<?= $e((string) $c['collab_altres']) ?>)</em>
              <?php endif; ?></td>
          </tr>
        <?php endforeach; ?>
        </tbody>
      </table>
      </div>
    <?php endif; ?>
  </section>

<?php endif; ?>
</main>

<footer>
  Els percentatges es calculen sobre el total de respostes. A les preguntes de
  resposta múltiple la suma pot superar el 100&nbsp;%.
</footer>
</body>
</html>
