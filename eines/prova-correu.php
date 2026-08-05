#!/usr/bin/env php
<?php
/**
 * Prova de l'enviament de correu.
 *
 * S'executa al servidor, per línia d'ordres:
 *     sudo -u www-data php eines/prova-correu.php
 *
 * Mostra el diàleg complet amb el servidor SMTP, de manera que si falla es
 * veu exactament per què (credencials, port bloquejat, remitent no autoritzat…).
 */

declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    http_response_code(403);
    exit("Aquesta eina només es pot executar per línia d'ordres.\n");
}

require_once __DIR__ . '/../api/lib/bootstrap.php';

$cfg  = aamo_config();
$smtp = $cfg['smtp'] ?? [];

echo "── Configuració llegida ──────────────────────────────────────\n";
printf("  servidor    : %s:%s (%s)\n",
    $smtp['host'] ?: '(buit)', $smtp['port'] ?? '?', $smtp['seguretat'] ?? '?');
printf("  usuari      : %s\n", $smtp['usuari'] ?: '(buit)');
printf("  contrasenya : %s\n", empty($smtp['contrasenya'])
    ? '(buida)'
    : str_repeat('*', 8) . ' (' . strlen((string) $smtp['contrasenya']) . ' caràcters)');
printf("  remitent    : %s\n", $smtp['remitent'] ?: '(buit)');
printf("  destinatari : %s\n", $cfg['desti_avisos']);
printf("  dades a     : %s\n", $cfg['dir_dades']);
printf("  panell      : %s\n", empty($cfg['admin_hash'])
    ? 'SENSE CONTRASENYA (admin_hash buit)'
    : 'contrasenya configurada');
echo "\n";

if (empty($smtp['host']) || empty($smtp['usuari']) || empty($smtp['contrasenya'])) {
    fwrite(STDERR, "L'SMTP no està configurat. Omple /var/www/musicaolerdola-privat/config.php\n");
    exit(1);
}

$autoload = __DIR__ . '/../api/vendor/autoload.php';
if (!is_readable($autoload)) {
    fwrite(STDERR, "Falta api/vendor/. Executa: cd api && composer install\n");
    exit(1);
}
require_once $autoload;

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception as PHPMailerException;

echo "── Diàleg amb el servidor SMTP ───────────────────────────────\n";

$mail = new PHPMailer(true);
$mail->SMTPDebug   = 2;
$mail->Debugoutput = 'echo';

try {
    $mail->isSMTP();
    $mail->Host       = (string) $smtp['host'];
    $mail->Port       = (int) ($smtp['port'] ?? 587);
    $mail->SMTPAuth   = true;
    $mail->Username   = (string) $smtp['usuari'];
    $mail->Password   = (string) $smtp['contrasenya'];
    $mail->SMTPSecure = ($smtp['seguretat'] ?? 'tls') === 'ssl'
        ? PHPMailer::ENCRYPTION_SMTPS
        : PHPMailer::ENCRYPTION_STARTTLS;
    $mail->CharSet = 'UTF-8';
    $mail->Timeout = 20;

    $mail->setFrom(
        (string) ($smtp['remitent'] ?: $smtp['usuari']),
        (string) ($smtp['nom_remitent'] ?? 'Web musicaolerdola.cat')
    );
    $mail->addAddress((string) $cfg['desti_avisos']);
    $mail->Subject = 'Prova d\'enviament — musicaolerdola.cat';
    $mail->isHTML(true);
    $mail->Body = '<p>Si llegeixes això, el correu del web ja funciona. &#9835;</p>'
        . '<p>Enviat el ' . date('d/m/Y \a \l\e\s H:i') . '.</p>';
    $mail->AltBody = 'Si llegeixes això, el correu del web ja funciona.';

    $mail->send();

    echo "\n✔ CORREU ENVIAT correctament a {$cfg['desti_avisos']}\n";
    echo "  Mira la safata d'entrada (i la de correu brossa el primer cop).\n";
    exit(0);
} catch (PHPMailerException) {
    echo "\n✘ NO S'HA POGUT ENVIAR\n";
    echo '  ' . $mail->ErrorInfo . "\n\n";
    echo "  Pistes segons l'error:\n";
    echo "  · «SmtpClientAuthentication is disabled» → el proveïdor ha desactivat\n";
    echo "    l'autenticació per contrasenya (és el cas d'Outlook.com). Cal canviar\n";
    echo "    de proveïdor: mira els comentaris d'api/config.example.php.\n";
    echo "  · «Username and Password not accepted» → a Gmail cal una contrasenya\n";
    echo "    d'aplicació, no la del compte.\n";
    echo "  · «Could not connect» → port tancat o servidor mal escrit.\n";
    echo "  · «From address not verified» → cal verificar el remitent al proveïdor.\n";
    exit(1);
}
