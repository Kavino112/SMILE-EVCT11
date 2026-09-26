# AlphaESS Wallbox Bridge

Home-Assistant-Integration für AlphaESS-Wallboxen der Reihe SMILE-EVCT11. Sie verwendet den aktuellen AlphaESS-Kundenportalzugang und legt die Zugangsdaten ausschließlich im geschützten Konfigurationsspeicher von Home Assistant ab.

> Dieses Projekt ist nicht offiziell von AlphaESS. Die Portal-Schnittstelle kann sich jederzeit ändern. Nutze die Steuerfunktionen nur, wenn du den aktuellen Zustand der Wallbox und der Hausinstallation kennst.

## Funktionen

- Status und aktuelle Ladeleistung
- Lademodus: ECO, Langsam-, Schon-, Schnell- und kundenspezifische Ladung
- Kundenspezifischer Ladestrom von 6 bis 16 A
- Lade-Start und Lade-Stopp mit aktueller Zustandsprüfung
- Seriennummer, Modell, Phasenwahl, Startleistung sowie Software- und Hardwarestand

Die Steuerung erhält vorhandene Zeitfenster und übrige Anlagenwerte beim Aktualisieren der Wallbox-Konfiguration.

## Installation

1. Lade den Ordner `custom_components/alphaess_portal_bridge` in dein Home-Assistant-Konfigurationsverzeichnis hoch.
2. Starte Home Assistant neu.
3. Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen** und wähle **AlphaESS Wallbox Bridge**.
4. Gib die E-Mail-Adresse, das Kennwort des AlphaESS-Kundenportals und die Seriennummer der Anlage ein. Die Anlagen-Seriennummer beginnt üblicherweise mit `ALB`.
5. Öffne anschließend **Neu konfigurieren** bei der Integration und ergänze die Wallbox-Seriennummer. Sie beginnt mit `ALP`.

Das Kennwort wird nicht protokolliert. 

## Bedienung

- Der Lademodus erscheint als Auswahl auf dem Wallbox-Gerät.
- Der Stromregler wird nur bei **Kundenspezifische Ladung** freigeschaltet.
- Start und Stopp sind nur verfügbar, wenn der Live-Status der Wallbox den jeweiligen Befehl zulässt.

## Voraussetzungen

- Home Assistant 2026.3 oder neuer
- Ein funktionierender Zugang zum AlphaESS-Kundenportal
- Eine im Portal mit der Anlage verknüpfte SMILE-EVCT11-Wallbox

## Mitwirken

Fehlerberichte mit Home-Assistant-Version, Wallbox-Modell und anonymisierten Protokollauszügen sind willkommen. Bitte keine Kennwörter, Tokens, Seriennummern oder vollständigen Portalantworten veröffentlichen.
