// Interaktive Vorbereitungs-Checkliste – E-Ink-Modus
// Läuft sofort (Script am Ende des Body, DOM bereits verfügbar)
// Zustand: localStorage pp-c-{stueck_id}

(function () {
  function renderChecklist(anzeige, text, id) {
    const gespeichert = new Set(JSON.parse(localStorage.getItem('pp-c-' + id) || '[]'));
    anzeige.innerHTML = '';

    text.split('\n').forEach(function (zeile, i) {
      const bereinigt = zeile.trim();
      if (!bereinigt) return;

      const istBullet = bereinigt.charAt(0) === '•'; // •
      const displayText = istBullet ? bereinigt.slice(1).trim() : bereinigt;

      const el = document.createElement('div');
      el.className = 'vcheck-item' + (gespeichert.has(i) ? ' done' : '');
      el.setAttribute('data-i', i);

      const mark = document.createElement('span');
      mark.className = 'vcheck-mark';

      const span = document.createElement('span');
      span.className = 'vcheck-text';
      span.textContent = displayText;

      el.appendChild(mark);
      el.appendChild(span);
      anzeige.appendChild(el);
    });

    // Klick-Handler per Event-Delegation
    anzeige.onclick = function (e) {
      var item = e.target;
      // Climb up to find .vcheck-item
      while (item && item !== anzeige) {
        if (item.className && item.className.indexOf('vcheck-item') !== -1) break;
        item = item.parentElement;
      }
      if (!item || item === anzeige) return;

      var done = item.className.indexOf(' done') !== -1;
      item.className = done
        ? item.className.replace(' done', '')
        : item.className + ' done';

      var aktiv = [];
      var alle = anzeige.querySelectorAll('.vcheck-item');
      for (var j = 0; j < alle.length; j++) {
        if (alle[j].className.indexOf(' done') !== -1) {
          aktiv.push(Number(alle[j].getAttribute('data-i')));
        }
      }
      localStorage.setItem('pp-c-' + id, JSON.stringify(aktiv));
    };
  }

  // Alle Checklisten initialisieren
  var anzeigen = document.querySelectorAll('.vcheck-anzeige[data-stueck-id]');
  for (var k = 0; k < anzeigen.length; k++) {
    var anzeige = anzeigen[k];
    var id = anzeige.getAttribute('data-stueck-id');
    var container = anzeige.parentElement;
    var ta = container ? container.querySelector('.vcheck-quelle') : null;
    if (ta) renderChecklist(anzeige, ta.value, id);
  }

  // Reset-Button
  var resetBtn = document.getElementById('checks-reset');
  if (resetBtn) {
    resetBtn.onclick = function (e) {
      e.preventDefault();
      if (!confirm('Alle Häkchen zurücksetzen?')) return;
      var keys = Object.keys(localStorage);
      for (var i = 0; i < keys.length; i++) {
        if (keys[i].indexOf('pp-c-') === 0) localStorage.removeItem(keys[i]);
      }
      location.reload();
    };
  }
})();
