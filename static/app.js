// ════════════════════════════════════════════════════════════════════════════
// 1. BULLET-TEXTAREAS – automatische Aufzählungszeichen
// ════════════════════════════════════════════════════════════════════════════
//
// Verhalten:
//   Enter   → neue Zeile mit gleichem Einzug + „• "  (nur wenn aktuelle
//             Zeile bereits ein Bullet hat; leeres Bullet beendet die Liste)
//   Tab     → Einzug um 2 Leerzeichen vertiefen
//   Shift+T → Einzug um 2 Leerzeichen verringern
//   Tipp:  „- " am Zeilenanfang wird automatisch zu „• "
//

function initBullets() {
  document.querySelectorAll('textarea[data-bullets]').forEach(ta => {
    ta.addEventListener('keydown', handleBulletKey);
    ta.addEventListener('input', handleBulletAutokonvert);
  });
}

function handleBulletKey(e) {
  const ta = e.target;
  const pos = ta.selectionStart;
  const text = ta.value;
  const zeilenAnfang = text.lastIndexOf('\n', pos - 1) + 1;
  const aktuelleZeile = text.substring(zeilenAnfang, pos);

  if (e.key === 'Enter') {
    e.preventDefault();
    // Prüfen ob aktuelle Zeile ein Bullet (mit optionalem Einzug) hat
    const match = aktuelleZeile.match(/^(\s*)•\s?/);
    if (match) {
      const einzug = match[1];
      if (aktuelleZeile.trim() === '•') {
        // Leeres Bullet → Liste beenden, Bullet entfernen
        const neuerText = text.substring(0, zeilenAnfang)
          + text.substring(zeilenAnfang + aktuelleZeile.length);
        ta.value = neuerText;
        ta.selectionStart = ta.selectionEnd = zeilenAnfang;
      } else {
        // Neues Bullet mit gleichem Einzug einfügen
        const einfuegen = '\n' + einzug + '• ';
        ta.value = text.substring(0, pos) + einfuegen + text.substring(pos);
        ta.selectionStart = ta.selectionEnd = pos + einfuegen.length;
      }
    } else {
      // Kein Bullet → normaler Zeilenumbruch
      ta.value = text.substring(0, pos) + '\n' + text.substring(pos);
      ta.selectionStart = ta.selectionEnd = pos + 1;
    }

  } else if (e.key === 'Tab') {
    e.preventDefault();
    if (e.shiftKey) {
      // Einzug verringern
      if (text.startsWith('  ', zeilenAnfang)) {
        ta.value = text.substring(0, zeilenAnfang) + text.substring(zeilenAnfang + 2);
        ta.selectionStart = ta.selectionEnd = Math.max(zeilenAnfang, pos - 2);
      }
    } else {
      // Einzug vertiefen
      ta.value = text.substring(0, zeilenAnfang) + '  ' + text.substring(zeilenAnfang);
      ta.selectionStart = ta.selectionEnd = pos + 2;
    }
  }
}

function handleBulletAutokonvert(e) {
  const ta = e.target;
  const pos = ta.selectionStart;
  const text = ta.value;
  const zeilenAnfang = text.lastIndexOf('\n', pos - 2) + 1;
  const bisKursor = text.substring(zeilenAnfang, pos);

  // „- " am Zeilenanfang → „• "
  if (bisKursor === '- ') {
    ta.value = text.substring(0, zeilenAnfang) + '• ' + text.substring(pos);
    ta.selectionStart = ta.selectionEnd = zeilenAnfang + 2;
  }
}


// ════════════════════════════════════════════════════════════════════════════
// 2. VORBEREITUNG-CHECKLISTE – Bullet-Punkte während der Probe abhaken
// ════════════════════════════════════════════════════════════════════════════
//
// Zustand (welche Zeilen abgehakt) wird im localStorage gespeichert.
// Schlüssel: pp-c-{stueck_id}  →  JSON-Array von Zeilennummern
//

function renderVcheck(anzeige, text, id) {
  const gespeichert = new Set(JSON.parse(localStorage.getItem('pp-c-' + id) || '[]'));
  anzeige.innerHTML = '';

  text.split('\n').forEach((zeile, i) => {
    const bereinigt = zeile.trim();
    if (!bereinigt) return;

    const istBullet = bereinigt.startsWith('•');
    const displayText = istBullet ? bereinigt.slice(1).trim() : bereinigt;
    const einzug = zeile.search(/\S/) / 2;

    const el = document.createElement('div');
    el.className = 'vcheck-item' + (gespeichert.has(i) ? ' done' : '');
    el.dataset.i = i;
    if (einzug > 0) el.style.paddingLeft = einzug + 'rem';

    const mark = document.createElement('span');
    mark.className = 'vcheck-mark';

    const span = document.createElement('span');
    span.className = 'vcheck-text';
    span.textContent = displayText;

    el.appendChild(mark);
    el.appendChild(span);
    anzeige.appendChild(el);
  });

  // Einmaliger Klick-Handler per Event-Delegation auf dem Container
  anzeige.onclick = function(e) {
    const item = e.target.closest('.vcheck-item');
    if (!item || !anzeige.contains(item)) return;
    item.classList.toggle('done');
    const aktiv = Array.from(anzeige.querySelectorAll('.vcheck-item.done'))
                       .map(el => Number(el.dataset.i));
    localStorage.setItem('pp-c-' + id, JSON.stringify(aktiv));
  };
}

function initVcheck() {
  document.querySelectorAll('.vcheck-anzeige[data-stueck-id]').forEach(anzeige => {
    const id = anzeige.dataset.stueckId;
    const ta = document.querySelector('.vcheck-quelle[data-stueck-id="' + id + '"]');
    if (ta) {
      ta.style.display = 'none';
      renderVcheck(anzeige, ta.value, id);
    }
  });
}

function vcheckToggle(btn) {
  const stueckCard = btn.closest('.stueck');
  const ta = stueckCard.querySelector('.vcheck-quelle');
  const anzeige = stueckCard.querySelector('.vcheck-anzeige');
  const editMode = ta.style.display !== 'none';

  if (editMode) {
    ta.style.display = 'none';
    anzeige.style.display = '';
    btn.textContent = '✎ Bearbeiten';
    renderVcheck(anzeige, ta.value, ta.dataset.stueckId);
  } else {
    ta.style.display = '';
    anzeige.style.display = 'none';
    btn.textContent = '✓ Fertig';
    ta.focus();
  }
}


// ════════════════════════════════════════════════════════════════════════════
// 3. FRAGEN-WIDGET – Checkboxen mit Speichern per fetch()
// ════════════════════════════════════════════════════════════════════════════
//
// Format im inhalt-Feld (eine Frage pro Zeile):
//   [ ] Offene Frage
//   [x] Geklärte Frage
//

const fragenZustand = new Map(); // abschnitt_id → [{text, erledigt}, ...]

function initFragen() {
  document.querySelectorAll('.fragen-widget').forEach(widget => {
    const id = widget.dataset.id;
    const rohdaten = widget.querySelector('.fragen-rohdaten').value || '';
    const fragen = parseFragen(rohdaten);
    fragenZustand.set(id, fragen);
    renderFragen(widget, id);

    const input = widget.querySelector('.frage-neu-input');
    const btn = widget.querySelector('.frage-hinzufuegen-btn');

    btn.addEventListener('click', () => frageHinzufuegen(widget, id));
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter') frageHinzufuegen(widget, id);
    });
  });
}

function parseFragen(text) {
  if (!text.trim()) return [];
  return text.split('\n')
    .filter(z => z.trim())
    .map(z => {
      if (z.startsWith('[x] ')) return { text: z.slice(4), erledigt: true };
      if (z.startsWith('[ ] ')) return { text: z.slice(4), erledigt: false };
      return { text: z, erledigt: false };
    });
}

function serialisiereFragen(fragen) {
  return fragen.map(f => (f.erledigt ? '[x] ' : '[ ] ') + f.text).join('\n');
}

function renderFragen(widget, id) {
  const fragen = fragenZustand.get(id) || [];
  const liste = widget.querySelector('.fragen-liste');
  liste.innerHTML = '';

  fragen.forEach((frage, i) => {
    const zeile = document.createElement('div');
    zeile.className = 'frage-zeile' + (frage.erledigt ? ' erledigt' : '');

    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.id = `frage-${id}-${i}`;
    cb.checked = frage.erledigt;
    cb.addEventListener('change', () => {
      fragen[i].erledigt = cb.checked;
      speichereFragen(id);
      renderFragen(widget, id);
    });

    const label = document.createElement('label');
    label.htmlFor = cb.id;
    label.className = 'frage-text';
    label.textContent = frage.text;

    zeile.appendChild(cb);
    zeile.appendChild(label);
    liste.appendChild(zeile);
  });

  if (fragen.length === 0) {
    const hinweis = document.createElement('p');
    hinweis.className = 'leer-hinweis';
    hinweis.textContent = 'Noch keine Fragen eingetragen.';
    liste.appendChild(hinweis);
  }
}

function frageHinzufuegen(widget, id) {
  const input = widget.querySelector('.frage-neu-input');
  const text = input.value.trim();
  if (!text) return;
  const fragen = fragenZustand.get(id);
  fragen.push({ text, erledigt: false });
  input.value = '';
  input.focus();
  speichereFragen(id);
  renderFragen(widget, id);
}

async function speichereFragen(id) {
  const fragen = fragenZustand.get(id) || [];
  const inhalt = serialisiereFragen(fragen);
  try {
    await fetch(`/abschnitt/${id}/inhalt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ inhalt }),
    });
  } catch (err) {
    console.error('Fragen konnten nicht gespeichert werden:', err);
  }
}


// ════════════════════════════════════════════════════════════════════════════
// 4. REPERTOIRE – Inline-Bearbeitung
// ════════════════════════════════════════════════════════════════════════════

function probeBearbeiten() {
  const form = document.getElementById('probe-editform');
  form.hidden = false;
  form.scrollIntoView({ block: 'nearest' });
  document.getElementById('edit-titel').focus();
}

function probeBearbeitenAbbrechen() {
  document.getElementById('probe-editform').hidden = true;
}

function repBearbeiten(id) {
  document.querySelector(`#rep-${id} .rep-zeige`).style.display = 'none';
  document.getElementById(`rep-edit-${id}`).hidden = false;
  document.querySelector(`#rep-edit-${id} input[name="titel"]`).focus();
}

function repBearbeitenAbbrechen(id) {
  document.querySelector(`#rep-${id} .rep-zeige`).style.display = '';
  document.getElementById(`rep-edit-${id}`).hidden = true;
}


// ════════════════════════════════════════════════════════════════════════════
// Init
// ════════════════════════════════════════════════════════════════════════════

// ════════════════════════════════════════════════════════════════════════════
// 5. STÜCK-FORMULAR – Speichern ohne Seitenneuladen
// ════════════════════════════════════════════════════════════════════════════

function initStueckForms() {
  document.querySelectorAll('.stueck-form').forEach(form => {
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      const origText = btn.textContent;
      btn.disabled = true;
      try {
        const resp = await fetch(form.action, { method: 'POST', body: new FormData(form) });
        if (resp.ok || resp.redirected) {
          btn.textContent = '✓ Gespeichert';
          btn.style.color = 'var(--farbe-akzent)';
        } else {
          throw new Error();
        }
      } catch {
        btn.textContent = '✗ Fehler';
        btn.style.color = '#b91c1c';
      } finally {
        btn.disabled = false;
        setTimeout(() => {
          btn.textContent = origText;
          btn.style.color = '';
        }, 2000);
      }
    });
  });
}


document.addEventListener('DOMContentLoaded', () => {
  initBullets();
  initVcheck();
  initFragen();
  initStueckForms();
});
