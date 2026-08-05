<?php
/**
 * Enviament de correu centralitzat.
 *
 * Tota la configuració SMTP ve del fitxer de configuració privat, de manera
 * que cap credencial viu dins del codi ni dins de git.
 *
 * Funciona amb qualsevol proveïdor SMTP (Gmail amb contrasenya d'aplicació,
 * Brevo, Mailjet, SES...). Vegeu README.md → "Configurar el correu".
 */

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception as PHPMailerException;

/**
 * Envia un correu. No llança mai excepcions: retorna true/false i registra
 * l'error al log de PHP. Així, si el correu falla, l'operació que l'ha
 * demanat (per exemple, guardar una resposta de l'enquesta) no es perd.
 *
 * @param string      $assumpte
 * @param string      $cos_html
 * @param string      $cos_text
 * @param array{0:string,1:string}|null $respon_a  [correu, nom] per al Reply-To
 */
function aamo_envia_correu(
    string $assumpte,
    string $cos_html,
    string $cos_text,
    ?array $respon_a = null
): bool {
    $cfg  = aamo_config();
    $smtp = $cfg['smtp'] ?? [];

    if (empty($smtp['host']) || empty($smtp['usuari']) || empty($smtp['contrasenya'])) {
        error_log('AAMO: SMTP sense configurar; no s\'envia el correu.');
        return false;
    }

    if (!class_exists(PHPMailer::class)) {
        $autoload = __DIR__ . '/../vendor/autoload.php';
        if (!is_readable($autoload)) {
            error_log('AAMO: falta vendor/autoload.php (cal executar "composer install").');
            return false;
        }
        require_once $autoload;
    }

    $mail = new PHPMailer(true);

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
        $mail->CharSet    = 'UTF-8';
        $mail->Timeout    = 20;

        // El remitent ha de ser una adreça autoritzada pel proveïdor SMTP.
        $mail->setFrom(
            (string) ($smtp['remitent'] ?? $smtp['usuari']),
            (string) ($smtp['nom_remitent'] ?? 'Web musicaolerdola.cat')
        );
        $mail->addAddress((string) $cfg['desti_avisos']);

        if ($respon_a !== null && filter_var($respon_a[0], FILTER_VALIDATE_EMAIL)) {
            $mail->addReplyTo($respon_a[0], $respon_a[1]);
        }

        $mail->isHTML(true);
        $mail->Subject = $assumpte;
        $mail->Body    = $cos_html;
        $mail->AltBody = $cos_text;

        $mail->send();
        return true;
    } catch (PHPMailerException) {
        error_log('AAMO: error enviant el correu: ' . $mail->ErrorInfo);
        return false;
    }
}

/** Embolcalla contingut HTML amb l'estil de l'associació. */
function aamo_plantilla_correu(string $titol, string $contingut): string
{
    $titol = htmlspecialchars($titol, ENT_QUOTES, 'UTF-8');
    return <<<HTML
<!DOCTYPE html>
<html lang="ca">
<body style="margin:0;padding:24px;background:#faf8f4;font-family:Georgia,'Times New Roman',serif;color:#2a1a2a;">
  <div style="max-width:640px;margin:0 auto;background:#fffef9;border:1px solid rgba(106,45,107,.15);border-radius:8px;overflow:hidden;">
    <div style="background:#4a1942;padding:20px 28px;">
      <h1 style="margin:0;font-size:20px;color:#e8d48b;font-weight:normal;letter-spacing:.5px;">&#9835; $titol</h1>
      <p style="margin:4px 0 0;font-size:13px;color:rgba(255,255,255,.7);">Amics de la Música d'Ol&egrave;rdola</p>
    </div>
    <div style="padding:28px;">
      $contingut
    </div>
    <div style="background:#faf8f4;padding:14px 28px;border-top:1px solid rgba(106,45,107,.1);font-size:12px;color:#6b5a6b;">
      Correu autom&agrave;tic generat des de musicaolerdola.cat
    </div>
  </div>
</body>
</html>
HTML;
}
