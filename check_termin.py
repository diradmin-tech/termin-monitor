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


def choose(page, placeholder, value, step):
    """Öffnet das Dropdown mit dem Platzhalter und wählt die Option mit dem Text 'value'."""
    print(f"Schritt '{step}': öffne Dropdown '{placeholder}', wähle '{value}'")
    page.get_by_text(placeholder, exact=True).first.click(timeout=20_000)
    page.wait_for_timeout(800)
    try:
        page.get_by_role("option", name=value).first.click(timeout=5_000)
    except Exception:
        # Fallback: Text eintippen und mit Enter bestätigen
        page.keyboard.type(value)
        page.wait_for_timeout(800)
        page.keyboard.press("Enter")
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
                choose(page, "Dienststelle auswählen", ORT, "Dienststelle")
                choose(page, "Dienstleistung auswählen", DIENSTLEISTUNG, "Dienstleistung")
                # Weiter-Button, falls die Seite einen Schritt zum Bestätigen verlangt
                weiter = page.get_by_role("button", name=re.compile("Weiter|Nächste", re.I))
                if weiter.count():
                    print("Klicke 'Weiter'")
                    weiter.first.click(timeout=10_000)
                    page.wait_for_timeout(3000)
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
