from datetime import date

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

import models
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

# Bestehende DB um neue Spalten ergänzen (falls noch nicht vorhanden)
with engine.connect() as _conn:
    _st = [c["name"] for c in inspect(engine).get_columns("stuecke")]
    if "repertoire_id" not in _st:
        _conn.execute(text("ALTER TABLE stuecke ADD COLUMN repertoire_id INTEGER REFERENCES repertoire(id)"))
    if "probe_notizen" not in _st:
        _conn.execute(text("ALTER TABLE stuecke ADD COLUMN probe_notizen TEXT NOT NULL DEFAULT ''"))

    _ab = [c["name"] for c in inspect(engine).get_columns("probe_abschnitte")]
    if "notizen" not in _ab:
        _conn.execute(text("ALTER TABLE probe_abschnitte ADD COLUMN notizen TEXT NOT NULL DEFAULT ''"))

    _conn.commit()

app = FastAPI(title="Probenplaner")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class ReihenfolgePayload(BaseModel):
    ids: list[int]


class InhaltPayload(BaseModel):
    inhalt: str


def parse_fragen(inhalt: str) -> list[dict]:
    """Parst das Zeilen-Format '[ ] Text' / '[x] Text' in eine Liste von Dicts."""
    ergebnis = []
    for zeile in inhalt.split("\n"):
        zeile = zeile.strip()
        if not zeile:
            continue
        if zeile.startswith("[x] "):
            ergebnis.append({"text": zeile[4:], "erledigt": True})
        elif zeile.startswith("[ ] "):
            ergebnis.append({"text": zeile[4:], "erledigt": False})
        else:
            ergebnis.append({"text": zeile, "erledigt": False})
    return ergebnis


ABSCHNITT_TYPEN = ["informationen", "einspiel", "fragen"]
ABSCHNITT_LABEL = {
    "informationen": "Informationen",
    "einspiel": "Einspiel",
    "fragen": "Zu klärende Fragen",
}


# ── Startseite ──────────────────────────────────────────────────────────────

@app.get("/")
def startseite(request: Request, db: Session = Depends(get_db)):
    heute = date.today()
    alle = db.query(models.Probe).order_by(models.Probe.datum).all()
    kommende = [p for p in reversed(alle) if p.datum >= heute]
    vergangene = [p for p in reversed(alle) if p.datum < heute]
    return templates.TemplateResponse(request, "index.html", {
        "kommende_proben": kommende,
        "vergangene_proben": vergangene,
    })


# ── Probe erstellen ─────────────────────────────────────────────────────────

@app.post("/proben/neu")
def probe_erstellen(
    titel: str = Form(...),
    datum: date = Form(...),
    ort: str = Form(""),
    db: Session = Depends(get_db),
):
    probe = models.Probe(titel=titel, datum=datum, ort=ort or None)
    db.add(probe)
    db.flush()

    for typ in ABSCHNITT_TYPEN:
        db.add(models.ProbeAbschnitt(probe_id=probe.id, typ=typ, inhalt=""))

    db.commit()
    return RedirectResponse(url=f"/probe/{probe.id}", status_code=303)


# ── Druckansicht ────────────────────────────────────────────────────────────

@app.get("/probe/{probe_id}/drucken")
def probe_drucken(probe_id: int, request: Request, db: Session = Depends(get_db)):
    probe = db.query(models.Probe).filter(models.Probe.id == probe_id).first()
    if not probe:
        raise HTTPException(status_code=404, detail="Probe nicht gefunden")

    abschnitte_map = {a.typ: a for a in probe.abschnitte}
    abschnitte_geordnet = [
        abschnitte_map[typ] for typ in ABSCHNITT_TYPEN if typ in abschnitte_map
    ]
    fragen_abschnitt = abschnitte_map.get("fragen")

    return templates.TemplateResponse(
        request,
        "probe_druck.html",
        {
            "probe": probe,
            "abschnitte": abschnitte_geordnet,
            "abschnitt_label": ABSCHNITT_LABEL,
            "fragen": parse_fragen(fragen_abschnitt.inhalt) if fragen_abschnitt else [],
        },
    )


# ── Probe bearbeiten ────────────────────────────────────────────────────────

@app.post("/probe/{probe_id}/bearbeiten")
def probe_bearbeiten(
    probe_id: int,
    titel: str = Form(...),
    datum: date = Form(...),
    ort: str = Form(""),
    db: Session = Depends(get_db),
):
    probe = db.query(models.Probe).filter(models.Probe.id == probe_id).first()
    if not probe:
        raise HTTPException(status_code=404, detail="Probe nicht gefunden")
    probe.titel = titel
    probe.datum = datum
    probe.ort = ort or None
    db.commit()
    return RedirectResponse(url=f"/probe/{probe_id}", status_code=303)


# ── Probe löschen ────────────────────────────────────────────────────────────

@app.post("/probe/{probe_id}/loeschen")
def probe_loeschen(probe_id: int, db: Session = Depends(get_db)):
    probe = db.query(models.Probe).filter(models.Probe.id == probe_id).first()
    if not probe:
        raise HTTPException(status_code=404, detail="Probe nicht gefunden")
    db.delete(probe)  # cascade löscht Abschnitte und Stücke automatisch
    db.commit()
    return RedirectResponse(url="/", status_code=303)


# ── Probe anzeigen ──────────────────────────────────────────────────────────

@app.get("/probe/{probe_id}")
def probe_detail(
    probe_id: int,
    request: Request,
    eink: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    probe = db.query(models.Probe).filter(models.Probe.id == probe_id).first()
    if not probe:
        raise HTTPException(status_code=404, detail="Probe nicht gefunden")

    abschnitte_map = {a.typ: a for a in probe.abschnitte}
    abschnitte_geordnet = [
        abschnitte_map[typ]
        for typ in ABSCHNITT_TYPEN
        if typ in abschnitte_map
    ]

    if eink:
        fragen_abschnitt = abschnitte_map.get("fragen")
        return templates.TemplateResponse(
            request,
            "probe_eink.html",
            {
                "probe": probe,
                "abschnitte": abschnitte_geordnet,
                "abschnitt_label": ABSCHNITT_LABEL,
                "fragen": parse_fragen(fragen_abschnitt.inhalt) if fragen_abschnitt else [],
                "fragen_abschnitt": fragen_abschnitt,
            },
        )

    # Aktive Repertoire-Stücke, die noch nicht in dieser Probe sind
    bereits_ids = {s.repertoire_id for s in probe.stuecke if s.repertoire_id}
    verfuegbare = (
        db.query(models.RepertoireStuck)
        .filter(
            models.RepertoireStuck.aktiv == True,
            ~models.RepertoireStuck.id.in_(bereits_ids),
        )
        .order_by(models.RepertoireStuck.titel)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "probe.html",
        {
            "probe": probe,
            "abschnitte": abschnitte_geordnet,
            "abschnitt_label": ABSCHNITT_LABEL,
            "verfuegbare_stuecke": verfuegbare,
        },
    )


# ── Abschnitt speichern ─────────────────────────────────────────────────────

@app.post("/abschnitt/{abschnitt_id}/speichern")
def abschnitt_speichern(
    abschnitt_id: int,
    inhalt: str = Form(""),
    db: Session = Depends(get_db),
):
    abschnitt = db.query(models.ProbeAbschnitt).filter(
        models.ProbeAbschnitt.id == abschnitt_id
    ).first()
    if not abschnitt:
        raise HTTPException(status_code=404, detail="Abschnitt nicht gefunden")
    abschnitt.inhalt = inhalt
    db.commit()
    return RedirectResponse(url=f"/probe/{abschnitt.probe_id}", status_code=303)


# ── Stück hinzufügen ────────────────────────────────────────────────────────

@app.post("/probe/{probe_id}/stueck/neu")
def stueck_hinzufuegen(
    probe_id: int,
    titel: str = Form(...),
    db: Session = Depends(get_db),
):
    probe = db.query(models.Probe).filter(models.Probe.id == probe_id).first()
    if not probe:
        raise HTTPException(status_code=404, detail="Probe nicht gefunden")

    naechste_position = len(probe.stuecke)
    stueck = models.Stueck(probe_id=probe_id, titel=titel, position=naechste_position)
    db.add(stueck)
    db.commit()
    return RedirectResponse(url=f"/probe/{probe_id}", status_code=303)


# ── Repertoire ──────────────────────────────────────────────────────────────

@app.get("/repertoire")
def repertoire_uebersicht(request: Request, db: Session = Depends(get_db)):
    alle = (
        db.query(models.RepertoireStuck)
        .order_by(models.RepertoireStuck.titel)
        .all()
    )
    aktive = [s for s in alle if s.aktiv]
    inaktive = [s for s in alle if not s.aktiv]
    return templates.TemplateResponse(
        request, "repertoire.html", {"aktive": aktive, "inaktive": inaktive}
    )


@app.post("/repertoire/neu")
def repertoire_neu(
    titel: str = Form(...),
    komponist: str = Form(""),
    db: Session = Depends(get_db),
):
    stuck = models.RepertoireStuck(titel=titel, komponist=komponist or None, aktiv=True)
    db.add(stuck)
    db.commit()
    return RedirectResponse(url="/repertoire", status_code=303)


@app.post("/repertoire/{rep_id}/toggle")
def repertoire_toggle(rep_id: int, db: Session = Depends(get_db)):
    stuck = db.query(models.RepertoireStuck).filter(models.RepertoireStuck.id == rep_id).first()
    if not stuck:
        raise HTTPException(status_code=404, detail="Stück nicht gefunden")
    stuck.aktiv = not stuck.aktiv
    db.commit()
    return RedirectResponse(url="/repertoire", status_code=303)


@app.post("/repertoire/{rep_id}/bearbeiten")
def repertoire_bearbeiten(
    rep_id: int,
    titel: str = Form(...),
    komponist: str = Form(""),
    db: Session = Depends(get_db),
):
    stuck = db.query(models.RepertoireStuck).filter(models.RepertoireStuck.id == rep_id).first()
    if not stuck:
        raise HTTPException(status_code=404, detail="Stück nicht gefunden")
    stuck.titel = titel
    stuck.komponist = komponist or None
    # Titel in allen Proben-Stücken, die auf diesen Eintrag referenzieren, mitziehen
    db.query(models.Stueck).filter(models.Stueck.repertoire_id == rep_id).update(
        {"titel": titel}
    )
    db.commit()
    return RedirectResponse(url="/repertoire", status_code=303)


@app.post("/repertoire/{rep_id}/loeschen")
def repertoire_loeschen(rep_id: int, db: Session = Depends(get_db)):
    stuck = db.query(models.RepertoireStuck).filter(models.RepertoireStuck.id == rep_id).first()
    if not stuck:
        raise HTTPException(status_code=404, detail="Stück nicht gefunden")
    # Verknüpfung in bestehenden Proben trennen, Stücke bleiben aber erhalten
    db.query(models.Stueck).filter(models.Stueck.repertoire_id == rep_id).update(
        {"repertoire_id": None}
    )
    db.delete(stuck)
    db.commit()
    return RedirectResponse(url="/repertoire", status_code=303)


# ── Stück nach oben / unten verschieben ────────────────────────────────────

@app.post("/stueck/{stueck_id}/verschieben")
def stueck_verschieben(
    stueck_id: int,
    richtung: str = Form(...),  # "hoch" | "runter"
    db: Session = Depends(get_db),
):
    stueck = db.query(models.Stueck).filter(models.Stueck.id == stueck_id).first()
    if not stueck:
        raise HTTPException(status_code=404, detail="Stück nicht gefunden")

    alle = (
        db.query(models.Stueck)
        .filter(models.Stueck.probe_id == stueck.probe_id)
        .order_by(models.Stueck.position)
        .all()
    )
    idx = next((i for i, s in enumerate(alle) if s.id == stueck_id), None)

    if richtung == "hoch" and idx and idx > 0:
        nachbar = alle[idx - 1]
        stueck.position, nachbar.position = nachbar.position, stueck.position
    elif richtung == "runter" and idx is not None and idx < len(alle) - 1:
        nachbar = alle[idx + 1]
        stueck.position, nachbar.position = nachbar.position, stueck.position

    db.commit()
    return RedirectResponse(url=f"/probe/{stueck.probe_id}", status_code=303)


# ── Abschnitt-Inhalt per JSON aktualisieren (für Fragen-Widget) ─────────────

@app.post("/abschnitt/{abschnitt_id}/inhalt")
def abschnitt_inhalt_aktualisieren(
    abschnitt_id: int,
    payload: InhaltPayload,
    db: Session = Depends(get_db),
):
    abschnitt = db.query(models.ProbeAbschnitt).filter(
        models.ProbeAbschnitt.id == abschnitt_id
    ).first()
    if not abschnitt:
        raise HTTPException(status_code=404, detail="Abschnitt nicht gefunden")
    abschnitt.inhalt = payload.inhalt
    db.commit()
    return {"ok": True}


# ── Stück aus Repertoire zur Probe hinzufügen ────────────────────────────────

@app.post("/probe/{probe_id}/stueck/aus-repertoire")
def stueck_aus_repertoire(
    probe_id: int,
    repertoire_id: int = Form(...),
    db: Session = Depends(get_db),
):
    probe = db.query(models.Probe).filter(models.Probe.id == probe_id).first()
    if not probe:
        raise HTTPException(status_code=404, detail="Probe nicht gefunden")
    rep = db.query(models.RepertoireStuck).filter(models.RepertoireStuck.id == repertoire_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Repertoire-Stück nicht gefunden")

    stueck = models.Stueck(
        probe_id=probe_id,
        titel=rep.titel,
        position=len(probe.stuecke),
        repertoire_id=repertoire_id,
    )
    db.add(stueck)
    db.commit()
    return RedirectResponse(url=f"/probe/{probe_id}", status_code=303)


# ── Abschnitt-Notizen speichern (separates Feld neben inhalt) ───────────────

@app.post("/abschnitt/{abschnitt_id}/notizen")
def abschnitt_notizen_speichern(
    abschnitt_id: int,
    notizen: str = Form(""),
    eink: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    abschnitt = db.query(models.ProbeAbschnitt).filter(
        models.ProbeAbschnitt.id == abschnitt_id
    ).first()
    if not abschnitt:
        raise HTTPException(status_code=404, detail="Abschnitt nicht gefunden")
    abschnitt.notizen = notizen
    db.commit()
    suffix = "?eink=1" if eink else ""
    return RedirectResponse(url=f"/probe/{abschnitt.probe_id}{suffix}", status_code=303)


# ── E-Ink: Fragen-Checkboxen speichern ─────────────────────────────────────

@app.post("/eink/abschnitt/{abschnitt_id}/fragen")
async def eink_fragen_speichern(abschnitt_id: int, request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    i, zeilen = 0, []
    while f"frage_text_{i}" in form:
        text = form[f"frage_text_{i}"]
        erledigt = f"frage_erledigt_{i}" in form
        zeilen.append(f"{'[x]' if erledigt else '[ ]'} {text}")
        i += 1
    abschnitt = db.query(models.ProbeAbschnitt).filter(
        models.ProbeAbschnitt.id == abschnitt_id
    ).first()
    if not abschnitt:
        raise HTTPException(status_code=404, detail="Abschnitt nicht gefunden")
    abschnitt.inhalt = "\n".join(zeilen)
    db.commit()
    return RedirectResponse(url=f"/probe/{abschnitt.probe_id}?eink=1", status_code=303)


# ── Stück aus Probe löschen ─────────────────────────────────────────────────

@app.post("/stueck/{stueck_id}/loeschen")
def stueck_loeschen(stueck_id: int, db: Session = Depends(get_db)):
    stueck = db.query(models.Stueck).filter(models.Stueck.id == stueck_id).first()
    if not stueck:
        raise HTTPException(status_code=404, detail="Stück nicht gefunden")
    probe_id = stueck.probe_id
    db.delete(stueck)
    db.commit()
    return RedirectResponse(url=f"/probe/{probe_id}", status_code=303)


# ── Stück-Notizen speichern ─────────────────────────────────────────────────

@app.post("/stueck/{stueck_id}/speichern")
def stueck_speichern(
    stueck_id: int,
    notizen: str = Form(""),
    probe_notizen: str = Form(""),
    eink: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    stueck = db.query(models.Stueck).filter(models.Stueck.id == stueck_id).first()
    if not stueck:
        raise HTTPException(status_code=404, detail="Stück nicht gefunden")
    stueck.notizen = notizen
    stueck.probe_notizen = probe_notizen
    db.commit()
    suffix = "?eink=1" if eink else ""
    return RedirectResponse(url=f"/probe/{stueck.probe_id}{suffix}", status_code=303)
