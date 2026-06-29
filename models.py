from sqlalchemy import Boolean, Column, Integer, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class RepertoireStuck(Base):
    __tablename__ = "repertoire"

    id = Column(Integer, primary_key=True, index=True)
    titel = Column(String, nullable=False)
    komponist = Column(String, nullable=True)
    aktiv = Column(Boolean, nullable=False, default=True)
    erstellt_am = Column(DateTime, server_default=func.now())

    probe_stuecke = relationship("Stueck", back_populates="repertoire_stuck")


class Probe(Base):
    __tablename__ = "proben"

    id = Column(Integer, primary_key=True, index=True)
    titel = Column(String, nullable=False)
    datum = Column(Date, nullable=False)
    ort = Column(String, nullable=True)
    erstellt_am = Column(DateTime, server_default=func.now())

    abschnitte = relationship(
        "ProbeAbschnitt",
        back_populates="probe",
        cascade="all, delete-orphan",
        order_by="ProbeAbschnitt.id",
    )
    stuecke = relationship(
        "Stueck",
        back_populates="probe",
        cascade="all, delete-orphan",
        order_by="Stueck.position",
    )


class ProbeAbschnitt(Base):
    """Die drei fixen Abschnitte jeder Probe: informationen, einspiel, fragen."""

    __tablename__ = "probe_abschnitte"

    id = Column(Integer, primary_key=True, index=True)
    probe_id = Column(Integer, ForeignKey("proben.id"), nullable=False)
    typ = Column(String, nullable=False)  # 'informationen' | 'einspiel' | 'fragen'
    inhalt = Column(Text, nullable=False, default="")
    notizen = Column(Text, nullable=False, default="")  # Antworten / freie Notizen

    probe = relationship("Probe", back_populates="abschnitte")


class Stueck(Base):
    __tablename__ = "stuecke"

    id = Column(Integer, primary_key=True, index=True)
    probe_id = Column(Integer, ForeignKey("proben.id"), nullable=False)
    titel = Column(String, nullable=False)
    position = Column(Integer, nullable=False, default=0)
    notizen = Column(Text, nullable=False, default="")
    probe_notizen = Column(Text, nullable=False, default="")
    repertoire_id = Column(Integer, ForeignKey("repertoire.id"), nullable=True)

    probe = relationship("Probe", back_populates="stuecke")
    repertoire_stuck = relationship("RepertoireStuck", back_populates="probe_stuecke")
