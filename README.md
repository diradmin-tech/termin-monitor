# Terminmonitor Amtsgericht Dortmund (Kirchenaustritt)

Prüft alle 15 Minuten die Terminseite von justiztermine.nrw.de in GitHub Actions
und sendet bei freien Terminen eine Push-Nachricht aufs Handy. Es wird **nicht**
automatisch gebucht. Der Code enthält keine persönlichen Daten und keine Zugangsdaten.

## Einrichtung (einmalig, ca. 10 Minuten)

### 1. ntfy auf dem Handy
- App „ntfy“ installieren (Android: Play Store, iPhone: App Store).
- Einen **schwer zu erratenden** Topic-Namen wählen, z. B. `termin-7f3k9q2x-dortmund`.
  Wer den Namen kennt, kann die Nachrichten mitlesen. Deshalb nicht öffentlich teilen.
- In der App das Topic abonnieren.

### 2. GitHub-Repository
- Konto auf github.com anlegen (falls noch nicht vorhanden).
- Neues Repository anlegen. **Öffentlich** wählen, damit die Actions kostenlos
  unbegrenzt laufen. Der Code ist dann für alle sichtbar, enthält aber nichts Persönliches.
- Diesen Ordner hochladen (Dateien und Ordner `.github/` mit hochladen).

### 3. Secrets setzen
Repository → **Settings → Secrets and variables → Actions → New repository secret**:

| Name         | Wert                                                              |
|--------------|-------------------------------------------------------------------|
| `TERMIN_URL` | URL der Seite „Datum auswählen“ (Schritt 3, aus der Adressleiste)  |
| `NTFY_TOPIC` | dein Topic-Name aus Schritt 1                                      |

### 4. Testen
- Repository → **Actions → Terminmonitor → Run workflow**.
- Im Lauf steht „Keine Termine.“ bzw. „TERMINE GEFUNDEN“.
- Ein roter (fehlgeschlagener) Lauf bedeutet: Seite unklar oder Fehler. GitHub schickt
  dann eine E-Mail.

## Hinweise
- **Nach der Buchung** den Workflow deaktivieren: Actions → Terminmonitor → „…“ → Disable workflow.
- Der Workflow läuft nur, solange das Repository aktiv ist. GitHub pausiert geplante Läufe
  nach 60 Tagen ohne Änderung am Repository.
- Geplante Läufe können sich um einige Minuten verzögern.
- Bei freien Terminen kommt die Nachricht bei jedem Lauf erneut, bis du gebucht oder
  deaktiviert hast.
- Lokal testen (optional): `pip install playwright`, `python -m playwright install chromium`,
  dann `TERMIN_URL=... NTFY_TOPIC=... python check_termin.py`.
