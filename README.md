# Probenplaner

Web-App zur Probenvorbereitung und Probenführung für Blasorchester. Selbst-gehostet, läuft als Docker-Container hinter einem Reverse Proxy.

## Funktionen

### Proben
- Proben anlegen, bearbeiten und löschen (Titel, Datum, Ort)
- Drei fixe Abschnitte pro Probe: **Informationen**, **Einspiel**, **Zu klärende Fragen**
- Fragen als interaktive Checkbox-Liste; geklärte Fragen werden durchgestrichen
- Separates Notizfeld für Antworten und Freitext pro Probe

### Stücke
- Stücke pro Probe frei hinzufügen oder aus dem **Repertoire** übernehmen
- Pro Stück: **Vorbereitungsnotizen** (vor der Probe) und **Probennotizen** (während der Probe)
- Reihenfolge per Pfeil-Buttons ändern (▲ / ▼)
- Einzelne Stücke aus der Probe entfernen

### Repertoire
- Zentrale Stückliste mit Titel und Komponist
- Status **aktiv / inaktiv** – nur aktive Stücke erscheinen in der Probe-Auswahl
- Titel-Änderungen werden automatisch in alle referenzierenden Proben übernommen
- Stücke bearbeiten und löschen

### Ansichten
| Ansicht | URL | Gerät |
|---|---|---|
| Normale Ansicht | `/probe/{id}` | Desktop / Tablet |
| **E-Ink-Modus** | `/probe/{id}?eink=1` | Boox Note Air 4c |
| **Druckansicht** | `/probe/{id}/drucken` | Browser-Druck |

### Textfelder
- Automatische Aufzählungszeichen: `- ` → `•`, Enter setzt neue Bullet-Zeile
- Einrückung mit Tab / Shift+Tab

### E-Ink-Modus
Optimiert für E-Ink-Displays (Boox Note Air 4c):
- Keine Animationen, kein Flicker
- 20px Basis-Schriftgrösse, hoher Kontrast (reines Schwarz/Weiss)
- Grosse Touch-Targets (min. 52px)
- Klappbare Abschnitte via `<details>` / `<summary>` (kein JavaScript)
- Nur die relevanten Felder sind editierbar (Probennotizen, Fragen-Checkboxen)

---

## Tech-Stack

| Schicht | Technologie |
|---|---|
| Backend | Python 3.12 + FastAPI |
| Datenbank | SQLite (eine Datei, kein separater Server) |
| Templates | Jinja2 |
| Frontend | Vanilla HTML + CSS + JavaScript |
| Deployment | Docker + docker-compose |

---

## Lokale Entwicklung

```bash
# Abhängigkeiten installieren
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# App starten (mit Auto-Reload bei Dateiänderungen)
uvicorn main:app --reload
```

Öffne anschliessend `http://localhost:8000` im Browser.

Die SQLite-Datenbank (`probenplaner.db`) wird beim ersten Start automatisch angelegt.

---

## Deployment mit Docker

### Voraussetzungen
- Proxmox LXC-Container (Ubuntu 22.04 / Debian 12) mit aktiviertem **Nesting**
- Docker installiert (`curl -fsSL https://get.docker.com | sh`)

### Starten

```bash
# Repo klonen
git clone https://github.com/alti4/probenplaner.git
cd probenplaner

# Datenbank-Verzeichnis anlegen
mkdir -p data

# Container bauen und starten
docker compose up -d

# Logs verfolgen
docker compose logs -f
```

Die App ist danach unter `http://<container-ip>:8000` erreichbar.

### Bestehende Daten übernehmen

```bash
cp probenplaner.db data/
```

### Updates einspielen

```bash
git pull
docker compose up -d --build
```

Die Daten in `./data/` bleiben dabei erhalten.

### Nginx Proxy Manager

| Feld | Wert |
|---|---|
| Scheme | `http` |
| Forward Hostname | IP des LXC-Containers |
| Forward Port | `8000` |

---

## Projektstruktur

```
probenplaner/
├── main.py              # FastAPI-App, alle Routen
├── models.py            # Datenbankmodelle (SQLAlchemy)
├── database.py          # SQLite-Verbindung
├── requirements.txt     # Python-Abhängigkeiten
├── Dockerfile
├── docker-compose.yml
├── static/
│   ├── style.css        # Haupt-Stylesheet
│   ├── eink.css         # E-Ink-Stylesheet
│   └── app.js           # Vanilla JavaScript
└── templates/
    ├── base.html        # Basis-Layout
    ├── index.html       # Startseite (Probenliste)
    ├── probe.html       # Probe-Detailseite
    ├── probe_eink.html  # E-Ink-Ansicht
    ├── probe_druck.html # Druckansicht
    └── repertoire.html  # Repertoire-Verwaltung
```
