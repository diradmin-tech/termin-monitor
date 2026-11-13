"""
Prüft einmal die Terminseite von justiztermine.nrw.de und sendet bei freien
Terminen eine Push-Nachricht über ntfy. Gedacht für GitHub Actions (ein Lauf
pro Aufruf, kein Dauerbetrieb). Bucht NICHT automatisch.

Benötigte Umgebungsvariablen:
    TERMIN_URL   URL der Seite "Datum auswählen" (Schritt 3)
    NTFY_TOPIC   geheimer ntfy-Topic-Name (wer ihn kennt, kann mitlesen)
Optional:
    NTFY_SERVER  Standard: https://ntfy.sh

Exit-Codes:
    0  keine Termine (oder Termine gefunden und Nachricht gesendet)
    1  Seite unklar, Ladefehler oder Benachrichtigung fehlgeschlagen
       (GitHub meldet fehlgeschlagene Läufe per E-Mail)
"""

import os
import re
import sys
import urllib.request

from playwright.sync_api import sync_playwright

START_URL = "https://www.justiztermine.nrw.de/"
ORT = "Amtsgericht Dortmund"
DIENSTLEISTUNG = "Kirchenaustritt"
NO_SLOTS_TEXT = "keine Termine mehr"
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b")  # Uhrzeiten deuten auf freie Slots hin


def click_text(page, label, step):
    """Klickt auf das erste sichtbare Element mit diesem Text."""
    print(f"Schritt '{step}': klicke '{label}'")
    page.get_by_text(label, exact=False).first.click(timeout=20_000)
    page.wait_for_timeout(2000)


def fetch_text(start_url, screenshot_path):
    """Öffnet die Startseite, wählt Ort und Dienstleistung und liefert den Text der Terminseite."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(start_url, wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(2000)
            try:
                click_text(page, ORT, "Ort")
                click_text(page, DIENSTLEISTUNG, "Dienstleistung")
            except Exception as exc:
                print(f"Auswahl fehlgeschlagen: {exc}")
                print("Seitentext an dieser Stelle:")
                print(" ".join(page.inner_text("body").split())[:1000])
                page.screenshot(path=screenshot_path, full_page=True)
                raise
            page.wait_for_timeout(2000)  # Terminseite nachladen lassen
            page.screenshot(path=screenshot_path, full_page=True)
            return page.inner_text("body")
        finally:
            browser.close()


def send_push(server, topic, title, message):
    req = urllib.request.Request(
        f"{server.rstrip('/')}/{topic}",
        data=message.encode("utf-8"),
        headers={"Title": title, "Priority": "urgent", "Tags": "rotating_light"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()


def main():
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").strip()
    if not topic:
        print("NTFY_TOPIC muss gesetzt sein.")
        return 1

    try:
        text = fetch_text(START_URL, "screenshot.png")
    except Exception as exc:
        print(f"Fehler beim Laden der Seite: {exc}")
        return 1

    if NO_SLOTS_TEXT in text:
        print("Keine Termine.")
        return 0

    if TIME_RE.search(text):
        print("TERMINE GEFUNDEN - sende Benachrichtigung.")
        try:
            send_push(
                server,
                topic,
                "Termin frei - Amtsgericht Dortmund",
                "Kirchenaustritt: Es sind Termine verfügbar. Jetzt schnell buchen!",
            )
        except Exception as exc:
            print(f"Benachrichtigung fehlgeschlagen: {exc}")
            return 1
        return 0

    print("Ergebnis unklar: weder 'keine Termine' noch Uhrzeiten gefunden. Seite prüfen.")
    print("--- Seitentext (Auszug) ---")
    print(" ".join(text.split())[:1000])
    print("--- Ende Auszug ---")
    return 1


if __name__ == "__main__":
    sys.exit(main())
