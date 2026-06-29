FROM python:3.12-slim

WORKDIR /app

# Abhängigkeiten zuerst kopieren – Docker cached diese Schicht solange
# sich requirements.txt nicht ändert (schnellere Rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode kopieren
COPY . .

# Datenbank-Verzeichnis anlegen (wird als Volume eingehängt)
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
