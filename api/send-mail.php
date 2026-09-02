<?php
/**
 * Formulari de contacte del web.
 *
 * Les credencials SMTP ja no viuen aquí: vénen del fitxer de configuració
 * privat (fora del webroot i fora de git). Vegeu README.md.
 *
 * Els missatges es desen també en local, de manera que si el correu falla
 * el missatge no es perd.
 */

declare(strict_types=1);

require_once __DIR__ . '/lib/bootstrap.php';
require_once __DIR__ . '/lib/mailer.php';

aamo_nomes_post();

// Camp trampa anti-robots (opcional al formulari).
if (aamo_text($_POST['web'] ?? '') !== '') {
    aamo_json(['success' => true, 'message' => 'Missatge enviat correctament']);
}

$visitant = aamo_hash_visitant();
if (!aamo_limit_peticions('cnt-' . $visitant, 5, 3600)) {
    aamo_error('Has enviat massa missatges seguits. Prova-ho més tard.', 429);
}

$nom      = aamo_text($_POST['nom'] ?? '', 120);
$email    = aamo_text($_POST['email'] ?? '', 180);
$missatge = aamo_text_llarg($_POST['missatge'] ?? '', 5000);

if ($nom === '' || $email === '' || $missatge === '') {
    aamo_error('Tots els camps són obligatoris');
}

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    aamo_error('Correu electrònic no vàlid');
}

// Desem primer: així cap missatge es perd si l'SMTP està caigut.
aamo_desa_registre('missatges.jsonl', [
    'data'     => date('c'),
    'nom'      => $nom,
    'email'    => $email,
    'missatge' => $missatge,
    'visitant' => $visitant,
]);

$e = fn(string $t): string => htmlspecialchars($t, ENT_QUOTES, 'UTF-8');

$html = aamo_plantilla_correu('Nou missatge des del web', '
    <table style="border-collapse:collapse;width:100%;font-size:14px;">
      <tr><td style="padding:8px 12px 8px 0;font-weight:bold;vertical-align:top;">Nom</td>
          <td style="padding:8px 0;">' . $e($nom) . '</td></tr>
      <tr><td style="padding:8px 12px 8px 0;font-weight:bold;vertical-align:top;">Correu</td>
          <td style="padding:8px 0;"><a href="mailto:' . $e($email) . '">' . $e($email) . '</a></td></tr>
      <tr><td style="padding:8px 12px 8px 0;font-weight:bold;vertical-align:top;">Missatge</td>
          <td style="padding:8px 0;">' . nl2br($e($missatge)) . '</td></tr>
    </table>
');

$text = "Nom: $nom\nCorreu: $email\n\nMissatge:\n$missatge\n";

if (aamo_envia_correu("Nou missatge del web - $nom", $html, $text, [$email, $nom])) {
    aamo_json(['success' => true, 'message' => 'Missatge enviat correctament']);
}

// El missatge està desat, però no s'ha pogut notificar.
aamo_error('No s\'ha pogut enviar el missatge. Escriu-nos directament a '
    . aamo_config()['desti_avisos'], 500);
