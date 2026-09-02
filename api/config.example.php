<?php
/**
 * PLANTILLA de configuració — aquest fitxer SÍ que és a git (no hi ha secrets).
 *
 * A producció, la còpia real viu a:
 *     /var/www/musicaolerdola-privat/config.php
 * amb permisos 0640 i propietari www-data. Aquell fitxer NO és a git i és
 * l'únic lloc on hi ha credencials.
 *
 * Per instal·lar-lo:
 *     sudo mkdir -p /var/www/musicaolerdola-privat/dades
 *     sudo cp api/config.example.php /var/www/musicaolerdola-privat/config.php
 *     sudo nano /var/www/musicaolerdola-privat/config.php     # omplir els valors
 *     sudo chown -R www-data:www-data /var/www/musicaolerdola-privat
 *     sudo chmod 750 /var/www/musicaolerdola-privat /var/www/musicaolerdola-privat/dades
 *     sudo chmod 640 /var/www/musicaolerdola-privat/config.php
 */

return [

    // ── Servidor de correu sortint ──────────────────────────────────────────
    //
    // IMPORTANT: l'SMTP d'Outlook.com JA NO FUNCIONA amb contrasenya.
    // Microsoft ha desactivat l'autenticació bàsica i només accepta OAuth2:
    //   535 5.7.139 SmtpClientAuthentication is disabled for the Mailbox
    //
    // Opció A — Gmail amb contrasenya d'aplicació (la més senzilla):
    //   1. El compte de Gmail ha de tenir la verificació en dos passos activada
    //   2. Anar a  https://myaccount.google.com/apppasswords
    //   3. Crear una contrasenya d'aplicació anomenada "web musicaolerdola"
    //   4. Copiar els 16 caràcters aquí sota (sense espais)
    //
    //   'host'        => 'smtp.gmail.com',
    //   'usuari'      => 'elmeucompte@gmail.com',
    //   'contrasenya' => 'xxxxxxxxxxxxxxxx',
    //   'remitent'    => 'elmeucompte@gmail.com',   // ha de ser el mateix compte
    //
    // Opció B — Brevo (300 correus/dia gratis, no depèn de cap compte personal):
    //   1. Crear compte a https://www.brevo.com
    //   2. SMTP & API → SMTP → copiar login i clau
    //
    //   'host'        => 'smtp-relay.brevo.com',
    //   'usuari'      => '9xxxxx@smtp-brevo.com',
    //   'contrasenya' => 'xsmtpsib-...',
    //   'remitent'    => 'musicaolerdola@outlook.com',  // verificat a Brevo
    //
    'smtp' => [
        'host'         => '',
        'port'         => 587,
        'seguretat'    => 'tls',        // 'tls' (port 587) o 'ssl' (port 465)
        'usuari'       => '',
        'contrasenya'  => '',
        'remitent'     => '',           // adreça autoritzada pel proveïdor
        'nom_remitent' => 'Web musicaolerdola.cat',
    ],

    // On arriben els avisos del formulari de contacte i de l'enquesta.
    'desti_avisos' => 'musicaolerdola@outlook.com',

    // Enviar un correu per cada resposta de l'enquesta.
    // Si es rep molt volum, es pot posar a false i consultar-ho al panell.
    'avisa_enquesta' => true,

    // Directori on es desen les respostes (ha de ser FORA del webroot).
    'dir_dades' => '/var/www/musicaolerdola-privat/dades',

    // ── Panell de resultats ─────────────────────────────────────────────────
    // Hash de la contrasenya d'accés a /api/admin.php.
    // Generar-lo al servidor amb:
    //     php -r 'echo password_hash("LA-TEVA-CONTRASENYA", PASSWORD_DEFAULT), PHP_EOL;'
    'admin_hash' => '',

    // Origen permès per a les peticions del formulari (CORS).
    'origen_permes' => 'https://musicaolerdola.cat',
];
