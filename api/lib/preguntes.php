<?php
/**
 * Definició de l'enquesta.
 *
 * Font única de veritat: assets/dades/preguntes.json. El mateix fitxer
 * l'utilitzen el formulari (JavaScript), la validació (aquest fitxer) i el
 * panell de resultats. Per canviar una pregunta només cal editar el JSON.
 */

declare(strict_types=1);

function aamo_definicio_enquesta(): array
{
    static $definicio = null;
    if ($definicio !== null) {
        return $definicio;
    }

    $ruta = __DIR__ . '/../../assets/dades/preguntes.json';
    $cru  = is_readable($ruta) ? file_get_contents($ruta) : false;
    $dades = $cru === false ? null : json_decode($cru, true);

    if (!is_array($dades) || empty($dades['passos'])) {
        error_log('AAMO: no s\'ha pogut llegir preguntes.json');
        $definicio = ['versio' => 0, 'passos' => [], 'collaboracio' => ['opcions' => []]];
        return $definicio;
    }

    $definicio = $dades;
    return $definicio;
}

/** Llista plana de preguntes, en l'ordre en què apareixen. */
function aamo_preguntes(): array
{
    $preguntes = [];
    foreach (aamo_definicio_enquesta()['passos'] as $pas) {
        foreach ($pas['preguntes'] ?? [] as $pregunta) {
            $preguntes[] = $pregunta;
        }
    }
    return $preguntes;
}
