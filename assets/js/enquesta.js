/* ═══════════════════════════════════════════════════════════════════════════
   Enquesta de participació — Amics de la Música d'Olèrdola

   El formulari es genera a partir d'assets/dades/preguntes.json, que és la
   font única de veritat (el mateix fitxer valida les dades al servidor).
   Per afegir o canviar una pregunta només cal editar aquell JSON.
   ═══════════════════════════════════════════════════════════════════════════ */

(() => {
  'use strict';

  const CLAU_DESAT = 'aamo-enquesta-v1';
  const RUTA_JSON = 'assets/dades/preguntes.json';
  const RUTA_API = 'api/enquesta.php';

  const $ = (sel, arrel = document) => arrel.querySelector(sel);

  const estat = {
    def: null,
    pantalla: 0,      // 0 = portada, 1..n = passos, n+1 = col·laboració
    totalPassos: 0,
    obertura: Date.now(),
    enviant: false,
  };

  const elements = {
    pantalles: $('#pantalles'),
    progres: $('#progres'),
    progresPlena: $('#progres-plena'),
    progresPas: $('#progres-pas'),
    progresPct: $('#progres-pct'),
    formulari: $('#formulari'),
    avisRecuperat: $('#avis-recuperat'),
    avisError: $('#avis-error'),
  };

  // ── Utilitats ─────────────────────────────────────────────────────────────
  const esc = (text) => String(text ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));

  /** Identificador vàlid per a atributs HTML. */
  const idNet = (text) => String(text).replace(/[^a-zA-Z0-9_-]/g, '_');

  // ── Construcció del formulari ─────────────────────────────────────────────
  function opcioHTML(pregunta, opcio, i) {
    const multiple = pregunta.tipus !== 'unica';
    const nom = multiple ? `${pregunta.id}[]` : pregunta.id;
    const id = `${idNet(pregunta.id)}_${i}`;
    return `
      <label class="opcio ${multiple ? 'multi' : 'unica'}" for="${id}">
        <input type="${multiple ? 'checkbox' : 'radio'}" id="${id}"
               name="${esc(nom)}" value="${esc(opcio)}">
        <span class="marca"></span>
        <span class="etiqueta">${esc(opcio)}</span>
      </label>`;
  }

  function comentariHTML(pregunta) {
    if (!pregunta.comentari) return '';
    const id = `${idNet(pregunta.id)}_com`;
    return `
      <div class="comentari">
        <button type="button" class="comentari-obre" data-obre="${id}">
          ＋ ${esc(pregunta.comentari)}
        </button>
        <div class="comentari-camp" id="${id}-caixa">
          <label class="camp" for="${id}">${esc(pregunta.comentari)}</label>
          <textarea id="${id}" name="${esc(pregunta.id)}_comentari"
                    placeholder="Escriu-hi el que vulguis…" maxlength="1000"></textarea>
        </div>
      </div>`;
  }

  function preguntaHTML(pregunta) {
    if (pregunta.tipus === 'text') {
      return `
        <div class="pregunta">
          <div class="pregunta-cap">
            <span class="pregunta-icona" aria-hidden="true">${esc(pregunta.icona || '♪')}</span>
            <div>
              <h3>${esc(pregunta.text)}</h3>
              ${pregunta.ajuda ? `<p class="ajuda">${esc(pregunta.ajuda)}</p>` : ''}
            </div>
          </div>
          <textarea name="${esc(pregunta.id)}" rows="6" maxlength="3000"
                    placeholder="Les teves idees ens interessen…"></textarea>
        </div>`;
    }

    const ajuda = pregunta.ajuda
      || (pregunta.tipus === 'unica' ? 'Tria una opció' : 'Pots marcar-ne més d\'una');

    return `
      <div class="pregunta">
        <div class="pregunta-cap">
          <span class="pregunta-icona" aria-hidden="true">${esc(pregunta.icona || '♪')}</span>
          <div>
            <h3>${esc(pregunta.text)}</h3>
            <p class="ajuda">${esc(ajuda)}</p>
          </div>
        </div>
        <div class="opcions">
          ${pregunta.opcions.map((o, i) => opcioHTML(pregunta, o, i)).join('')}
        </div>
        ${comentariHTML(pregunta)}
      </div>`;
  }

  function passoHTML(pas, index) {
    const darrer = index === estat.totalPassos - 1;
    return `
      <section class="pantalla" data-pantalla="${index + 1}">
        <div class="pas-cap">
          <h2>${esc(pas.titol)}</h2>
          <p>${esc(pas.subtitol || '')}</p>
        </div>
        ${pas.preguntes.map(preguntaHTML).join('')}
        <div class="navegacio">
          <button type="button" class="btn" data-anar="enrere">← Enrere</button>
          <button type="button" class="btn btn-principal" data-anar="endavant">
            ${darrer ? 'Continuar →' : 'Següent →'}
          </button>
        </div>
      </section>`;
  }

  function collaboracioHTML(c) {
    const opcions = (c.opcions || []).map((o, i) => `
      <label class="opcio multi" for="col_${i}">
        <input type="checkbox" id="col_${i}" name="collaboracio[]" value="${esc(o)}">
        <span class="marca"></span>
        <span class="etiqueta">${esc(o)}</span>
      </label>`).join('');

    return `
      <section class="pantalla" data-pantalla="${estat.totalPassos + 1}">
        <div class="pas-cap">
          <h2>${esc(c.titol)}</h2>
          <p>${esc(c.subtitol)}</p>
        </div>

        <blockquote class="cita-portada">
          ${esc(c.cita)}
        </blockquote>

        <div class="pregunta">
          <div class="pregunta-cap">
            <span class="pregunta-icona" aria-hidden="true">✋</span>
            <div>
              <h3>${esc(c.text)}</h3>
              <p class="ajuda">Opcional — només si vols implicar-t'hi</p>
            </div>
          </div>
          <div class="opcions">${opcions}</div>
          <div class="comentari">
            <div class="comentari-camp oberta" id="col_altres-caixa" style="display:none">
              <label class="camp" for="col_altres">Explica'ns com</label>
              <input type="text" id="col_altres" name="collaboracio_altres"
                     maxlength="300" placeholder="En què t'agradaria ajudar?">
            </div>
          </div>
        </div>

        <div class="pregunta">
          <div class="pregunta-cap">
            <span class="pregunta-icona" aria-hidden="true">✉️</span>
            <div>
              <h3>Les teves dades de contacte</h3>
              <p class="ajuda">Només si vols que et puguem escriure</p>
            </div>
          </div>
          <div class="camp-grup">
            <label class="camp" for="nom">Nom i cognoms</label>
            <input type="text" id="nom" name="nom" maxlength="120" autocomplete="name"
                   placeholder="El teu nom">
          </div>
          <div class="camp-grup">
            <label class="camp" for="telefon">Telèfon mòbil</label>
            <input type="tel" id="telefon" name="telefon" maxlength="40" autocomplete="tel"
                   placeholder="600 00 00 00">
          </div>
          <div class="camp-grup">
            <label class="camp" for="email">Correu electrònic</label>
            <input type="email" id="email" name="email" maxlength="180" autocomplete="email"
                   placeholder="nom@exemple.cat">
          </div>
          <label class="consent" for="consentiment">
            <input type="checkbox" id="consentiment" name="consentiment" value="1">
            <span class="marca"></span>
            <span>Accepto que l'Associació guardi aquestes dades per contactar-me sobre
              les seves activitats. Pots consultar-ne els detalls a la
              <a href="privacitat.html" target="_blank" rel="noopener">política de privacitat</a>.</span>
          </label>
        </div>

        <div class="navegacio">
          <button type="button" class="btn" data-anar="enrere">← Enrere</button>
          <button type="submit" class="btn btn-principal" id="btn-enviar">
            Enviar l'enquesta ♪
          </button>
        </div>
      </section>`;
  }

  function finalHTML() {
    return `
      <section class="pantalla final" data-pantalla="${estat.totalPassos + 2}">
        <div class="final-icona">♥</div>
        <h2>Moltes gràcies!</h2>
        <p>La teva opinió ens ajudarà a construir una associació activa, oberta i
           participativa.</p>
        <p><em>Esperem escampar la música arreu del municipi!</em></p>
        <div class="accions-final">
          <a href="index.html" class="btn btn-principal">Tornar al web</a>
          <a href="index.html#contacte" class="btn">Contactar-nos</a>
        </div>
      </section>`;
  }

  // ── Navegació ─────────────────────────────────────────────────────────────
  function mostra(index) {
    const pantalles = elements.pantalles.querySelectorAll('.pantalla');
    pantalles.forEach((p) => p.classList.remove('activa'));
    const objectiu = elements.pantalles.querySelector(`[data-pantalla="${index}"]`);
    if (!objectiu) return;
    objectiu.classList.add('activa');
    estat.pantalla = index;

    const esPregunta = index >= 1 && index <= estat.totalPassos + 1;
    elements.progres.classList.toggle('oculta', !esPregunta);

    if (esPregunta) {
      const total = estat.totalPassos + 1;
      const pct = Math.round((index / total) * 100);
      elements.progresPlena.style.width = `${pct}%`;
      elements.progresPas.textContent = `Pas ${index} de ${total}`;
      elements.progresPct.textContent = `${pct}%`;
    }

    amagaError();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function mostraError(missatge) {
    elements.avisError.textContent = missatge;
    elements.avisError.classList.remove('oculta');
    elements.avisError.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function amagaError() {
    elements.avisError.classList.add('oculta');
  }

  // ── Desat automàtic ───────────────────────────────────────────────────────
  function recull() {
    const dades = {};
    new FormData(elements.formulari).forEach((valor, clau) => {
      if (clau === 'web' || clau === 'obertura') return;
      if (clau.endsWith('[]')) {
        const k = clau.slice(0, -2);
        (dades[k] ??= []).push(valor);
      } else {
        dades[clau] = valor;
      }
    });
    return dades;
  }

  function desa() {
    try {
      localStorage.setItem(CLAU_DESAT, JSON.stringify({
        quan: Date.now(),
        pantalla: estat.pantalla,
        dades: recull(),
      }));
    } catch { /* mode privat o quota exhaurida: no passa res */ }
  }

  function esborraDesat() {
    try { localStorage.removeItem(CLAU_DESAT); } catch { /* ignorable */ }
  }

  function llegeixDesat() {
    try {
      const cru = localStorage.getItem(CLAU_DESAT);
      if (!cru) return null;
      const desat = JSON.parse(cru);
      // Descartem esborranys de fa més de 7 dies.
      if (!desat?.dades || Date.now() - (desat.quan || 0) > 7 * 864e5) {
        esborraDesat();
        return null;
      }
      return desat;
    } catch {
      return null;
    }
  }

  function aplica(dades) {
    Object.entries(dades).forEach(([clau, valor]) => {
      const valors = Array.isArray(valor) ? valor : [valor];
      const camps = elements.formulari.querySelectorAll(
        `[name="${clau}"], [name="${clau}[]"]`
      );
      camps.forEach((camp) => {
        if (camp.type === 'checkbox' || camp.type === 'radio') {
          if (valors.includes(camp.value)) camp.checked = true;
        } else if (valors[0] !== undefined) {
          camp.value = valors[0];
          if (camp.value.trim() !== '') obreComentariDe(camp);
        }
      });
    });
    actualitzaAltres();
  }

  /** Si un comentari recuperat té text, el desplega perquè es vegi. */
  function obreComentariDe(camp) {
    const caixa = camp.closest('.comentari-camp');
    if (!caixa) return;
    caixa.classList.add('oberta');
    const boto = caixa.parentElement?.querySelector('.comentari-obre');
    boto?.classList.add('amagat');
  }

  /** Mostra el camp lliure de col·laboració només si s'ha marcat "Altres". */
  function actualitzaAltres() {
    const caixa = document.getElementById('col_altres-caixa');
    if (!caixa) return;
    const marcat = [...elements.formulari.querySelectorAll('[name="collaboracio[]"]')]
      .some((c) => c.checked && /^altres$/i.test(c.value.trim()));
    caixa.style.display = marcat ? 'block' : 'none';
  }

  // ── Validació del bloc de contacte ────────────────────────────────────────
  function validaContacte() {
    const nom = $('#nom')?.value.trim() || '';
    const tel = $('#telefon')?.value.trim() || '';
    const mail = $('#email')?.value.trim() || '';
    const consent = $('#consentiment')?.checked || false;
    const collab = [...elements.formulari.querySelectorAll('[name="collaboracio[]"]')]
      .some((c) => c.checked);

    if (!nom && !tel && !mail && !collab) return true; // pas opcional, buit

    if (!consent) {
      return 'Per deixar-nos les teves dades cal acceptar la política de privacitat.';
    }
    if (!nom) {
      return 'Cal indicar el nom i els cognoms.';
    }
    if (!mail && !tel) {
      return 'Deixa\'ns un correu electrònic o un telèfon per poder-te contactar.';
    }
    if (mail && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(mail)) {
      return 'El correu electrònic no sembla correcte.';
    }
    return true;
  }

  function hiHaAlgunaResposta() {
    const dades = recull();
    return Object.entries(dades).some(([clau, valor]) => {
      if (['nom', 'telefon', 'email', 'consentiment', 'collaboracio',
        'collaboracio_altres'].includes(clau)) return false;
      return Array.isArray(valor) ? valor.length > 0 : String(valor).trim() !== '';
    });
  }

  // ── Enviament ─────────────────────────────────────────────────────────────
  async function envia(event) {
    event.preventDefault();
    if (estat.enviant) return;

    const validesa = validaContacte();
    if (validesa !== true) {
      mostraError(validesa);
      return;
    }
    if (!hiHaAlgunaResposta()) {
      mostraError('Contesta almenys una pregunta abans d\'enviar l\'enquesta.');
      return;
    }

    const boto = $('#btn-enviar');
    const textOriginal = boto.textContent;
    estat.enviant = true;
    boto.disabled = true;
    boto.textContent = 'Enviant…';
    amagaError();

    const cos = new FormData(elements.formulari);
    cos.set('obertura', String(estat.obertura));

    try {
      const resposta = await fetch(RUTA_API, { method: 'POST', body: cos });
      const dades = await resposta.json().catch(() => ({}));

      if (resposta.ok && dades.success) {
        esborraDesat();
        mostra(estat.totalPassos + 2);
        return;
      }
      mostraError(dades.error || 'No s\'ha pogut enviar l\'enquesta. Torna-ho a provar.');
    } catch {
      mostraError('Sense connexió amb el servidor. Comprova la xarxa i torna-ho a provar.');
    } finally {
      estat.enviant = false;
      boto.disabled = false;
      boto.textContent = textOriginal;
    }
  }

  // ── Arrencada ─────────────────────────────────────────────────────────────
  async function inicia() {
    let def;
    try {
      const resposta = await fetch(RUTA_JSON, { cache: 'no-cache' });
      def = await resposta.json();
    } catch {
      elements.pantalles.innerHTML = `
        <div class="avis avis-error">
          No s'han pogut carregar les preguntes. Recarrega la pàgina, si us plau.
        </div>`;
      return;
    }

    estat.def = def;
    estat.totalPassos = def.passos.length;

    // Portada + passos + col·laboració + pantalla final
    elements.pantalles.insertAdjacentHTML('beforeend',
      def.passos.map(passoHTML).join('')
      + collaboracioHTML(def.collaboracio)
      + finalHTML());

    $('#intro-text').textContent = def.intro || '';

    // Recuperació d'un esborrany anterior
    const desat = llegeixDesat();
    if (desat) {
      aplica(desat.dades);
      elements.avisRecuperat.classList.remove('oculta');
    }

    // ── Escoltadors ──
    elements.pantalles.addEventListener('click', (e) => {
      const anar = e.target.closest('[data-anar]');
      if (anar) {
        const seguent = anar.dataset.anar === 'endavant'
          ? estat.pantalla + 1
          : estat.pantalla - 1;
        mostra(Math.max(0, seguent));
        return;
      }

      const obre = e.target.closest('.comentari-obre');
      if (obre) {
        document.getElementById(`${obre.dataset.obre}-caixa`)?.classList.add('oberta');
        obre.classList.add('amagat');
        document.getElementById(obre.dataset.obre)?.focus();
      }
    });

    elements.formulari.addEventListener('change', () => {
      actualitzaAltres();
      desa();
    });
    elements.formulari.addEventListener('input', desa);
    elements.formulari.addEventListener('submit', envia);

    $('#btn-comenca').addEventListener('click', () => mostra(1));
    $('#btn-descarta').addEventListener('click', () => {
      esborraDesat();
      location.reload();
    });

    // Evitem que Enter enviï el formulari abans d'hora.
    elements.formulari.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA'
        && e.target.type !== 'submit') {
        e.preventDefault();
        if (estat.pantalla <= estat.totalPassos) mostra(estat.pantalla + 1);
      }
    });

    mostra(desat?.pantalla > 0 ? Math.min(desat.pantalla, estat.totalPassos + 1) : 0);
  }

  document.addEventListener('DOMContentLoaded', inicia);
})();
