[中文](README.md) | [English](README.en.md) | [日本語](README.ja.md) | [Español](README.es.md) | **[Deutsch](README.de.md)**

# Red Sprite Filter

Ein macOS-Desktopwerkzeug für die Beobachtung transluzenter Höhenereignisse (TLE), das aus von Kameras aufgenommenen Gewittervideos automatisch verdächtige Frames und Clips von Red Sprites (roten Elfen) herausfiltert.

![macOS](https://img.shields.io/badge/macOS-12%2B-0b1220?style=flat-square)
![Release](https://img.shields.io/badge/download-DMG-00bcd4?style=flat-square)
![Local](https://img.shields.io/badge/processing-local-4caf50?style=flat-square)

## Was es macht

Red Sprites sind normalerweise kurz, schwach, hoch am Himmel und haben feine, komplexe Formen. Lange Videos manuell Frame für Frame zu durchsuchen, ist äußerst zeitaufwändig. Dieses Werkzeug scannt das gesamte Video, bewertet jeden Frame als Red-Sprite-Kandidat und exportiert automatisch:

- Kandidaten-Schlüsselframes
- Kandidaten-Kurzclips
- `candidates.csv`
- `contact_sheet.jpg`
- `report.html`
- `confirmed_candidates.csv` nach manueller Überprüfung

Es stoppt **nicht** beim ersten Kandidaten — es scannt das ganze Video und wählt dann die am höchsten bewerteten Kandidatenereignisse aus der gesamten Aufnahme aus.

## Oberflächenvorschau

Die aktuelle Version ist eine native macOS-Fenster-App, die eine WebView für die lokale Oberfläche nutzt. Es wird kein Browser geöffnet, und die Videobearbeitung wird niemals ins Netz hochgeladen.

Die Oberfläche umfasst:

- Video / Ordner / Ausgabeverzeichnis auswählen
- Präzises Filtern / Filter mit hohem Recall
- Raster der Kandidatenframes
- Wiedergabe von Kandidatenclips
- Manuelle Überprüfung: Bestätigen / Verdächtig / Ausschließen
- Bericht öffnen / Ergebnisordner öffnen

## Download

Lade aus dem Bereich **Releases** (rechts oder unten auf der Seite) herunter:

```text
red-sprite-filter-1.0.0.dmg
```

Öffne die DMG und ziehe die App (`红色精灵筛选器.app`, angezeigt als "Red Sprite Filter") in die Programme oder einen beliebigen Ordner.

## Beim ersten Start

Der aktuelle Build ist **nicht** mit einer Apple Developer ID signiert oder notariisiert, daher kann macOS eine Warnung „Entwickler nicht verifizieren“ anzeigen.

So öffnest du sie:

1. Rechtsklick auf `红色精灵筛选器.app`
2. „Öffnen“ wählen
3. Im Dialog erneut auf „Öffnen“ klicken

## Abhängigkeiten

Um das Paket klein zu halten, nutzt die aktuelle Version die lokale Laufzeitumgebung des Ziel-Macs wieder. Du benötigst:

- `python3`
- `ffmpeg`
- `ffprobe`
- `numpy`
- `Pillow`

Empfohlene Installation via Homebrew:

```bash
brew install ffmpeg
python3 -m pip install numpy Pillow
```

Die App prüft die Abhängigkeiten beim Start. Wenn du `ffmpeg not found` oder `ffprobe not found` siehst, stelle sicher, dass `ffmpeg` über Homebrew installiert ist.

## Empfohlene Nutzung

### Präzises Filtern eines einzelnen Videos

Geeignet, wenn du vermutest, dass ein bestimmtes Video Red Sprites eingefangen hat.

Empfohlene Parameter:

- Modus: Präzise
- Max. Kandidaten: 24
- Min. Score: 0.8
- Min. rote Pixel: 8
- Vorlauf: 1,0 s
- Nachlauf: 2,0 s

### Stapel-Vorfilterung eines Ordners

Geeignet, um schnell eine Charge Gewittermaterial zu prüfen.

Empfohlene Parameter:

- Modus: Hoher Recall
- Max. Kandidaten: 24
- Min. Score: 0.012
- Min. rote Pixel: 8

Nach der Vorfilterung einzeln die verdächtigen Videos im Modus „Präzise“ erneut ausführen.

## So erkennst du, ob ein Kandidat ein Red Sprite ist

Kandidaten, die eher wie Red Sprites aussehen, haben meist:

- eine Position über der Wolkenoberkante oder im oberen Bildbereich
- deutlich rot oder magentafarben
- eine lokale Form, kein rotes Glühen über den ganzen Horizont
- eine vertikale säulen-, faden-, quallen- oder feinverzweigte Struktur
- eine extrem kurze Dauer, meist nur in wenigen Frames deutlich sichtbar

Häufige Falschmeldungen (false positives) sind:

- gewöhnliche Wolken- oder Wolke-Erde-Blitze
- Stadtlichter, Scheinwerfer, Turmlichter, Flugzeuglichter
- rotes Horizontglühen
- Linsenreflexionen (Lens Flare)
- große Belichtungsänderungen
- feste Hotpixel oder Kompressionsrauschen

## Datenschutz

Alle Videos werden lokal auf deinem Rechner verarbeitet. Das Werkzeug lädt niemals Videos, Frames, Kandidatenclips oder Pfadinformationen hoch.

## Aktueller Stand

Dies ist eine frühe öffentliche Version eines Foto-Workflow-Werkzeugs. Es dient als Hilfe beim Filtern und ersetzt nicht die manuelle Überprüfung. Issues und Feedback sind willkommen — Falschmeldungen, übersehene Treffer, Verhalten bei verschiedenen Kameramodellen und Funktionsvorschläge.

## Roadmap

- Python und ffmpeg einbetten, um die Einstiegshürde zu senken
- Signierung und Notarisierung mit Apple Developer ID
- Scan feinerer Zeitbereiche unterstützen
- eine Zusammenfassungsansicht für Stapelergebnisse hinzufügen
- Filter-Schwellenwerte mit mehr echten Samples kalibrieren
