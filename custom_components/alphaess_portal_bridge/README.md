# AlphaESS Wallbox Bridge – Storion4you Community Build

> **Öffentliche Beta 0.5.2**  
> Gebaut für die Community von **https://www.storion4you.de/**  
> G2T-Erweiterung für **AlphaESS SMILE-G3-EVCT11/S**: **Kavino**  
> Basierend auf dem Ausgangsprojekt `wfa001/SMILE-EVCT11`.

Diese Home-Assistant-Custom-Integration bindet AlphaESS-Wallboxen über das AlphaESS-Kundenportal an Home Assistant an. Der Community-Build erweitert die bestehende G1T-Unterstützung um die neuere G2T-Konfiguration der SMILE-G3-EVCT11/S.

**Beta-Hinweis:** Dies ist keine offizielle AlphaESS-Integration. Die G2T-Funktionen wurden umfangreich praktisch getestet, einige Sonderfälle sind aber noch offen. Vor dem Update den bestehenden Integrationsordner sichern.

## Unterstützter Stand

### G2T – praktisch bestätigt

- automatische Erkennung des Portal-Profils `g2T`
- Live-Status und Ladeleistung
- Fahrzeug angeschlossen / Ladestecker verriegelt als Ja/Nein
- Ladeeinstellung: **Manuell / Zeitgesteuertes Aufladen / Plug and Play**
- Lademodus: **Langsamladung / Schonladung / Schnellladung / Kundenspezifische Ladeleistung**
- kundenspezifischer Ladestrom **6–16 A**
- OBC-Phasenwahl **1 / 2 / 3**
- Smart Mode mit Schutzprüfungen
- drei Zeitrahmen mit Aktivierung, Start, Ende, Lademodus und Maximalstrom
- Zeitwerte im vom Portal verwendeten **15-Minuten-Raster**
- Hausstrom-Einstellung **25–1000 A**
- Installateursteuerung erlaubt
- Kabel-Selbstverriegelung aktiviert
- Hardware-/Software-/Modell-/Profil-Diagnose
- Energie- und Ladeberichtswerte

### G1T

Die bestehende G1T-Erkennung und -Konfiguration des Ausgangsprojekts bleibt erhalten. Die neuen G2T-spezifischen Schutzregeln greifen nicht in den G1T-Pfad ein. Für diese Beta wurde jedoch **kein eigener G1T-Hardware-Regressionslauf** durchgeführt; Rückmeldungen von G1T-Testern sind ausdrücklich willkommen.

## Wichtige G2T-Schutzlogik

### Laden starten / stoppen

Bei G2T sind **Laden starten** und **Laden stoppen ausschließlich bei Ladeeinstellung „Manuell“ verfügbar**. Das wurde mit angeschlossenem Fahrzeug unter Last bestätigt.

Bei **Zeitgesteuertem Aufladen** und **Plug and Play** werden die Buttons deaktiviert. Zusätzlich blockiert die API-Schicht einen direkten Start-/Stop-Aufruf außerhalb des manuellen Modus. Damit wird verhindert, dass Home Assistant einen Befehl scheinbar erfolgreich ausführt, obwohl die aktive AlphaESS-Strategie ihn ignoriert.

### Smart Mode

Smart Mode wird nur bei G2T angeboten. Beim Aktivieren prüft die Integration:

- Zeitgesteuertes Aufladen darf nicht aktiv sein.
- OBC-Phasenwahl muss auf **3-phasig** stehen.
- Lademodus muss **Langsamladung, Schonladung oder Schnellladung** sein.

Ein Wechsel auf Zeitgesteuertes Aufladen bei aktivem Smart Mode wird ebenfalls blockiert. Ebenso muss Smart Mode vor einem manuellen Wechsel auf 1- oder 2-phasig deaktiviert werden.

## Bekannte Beta-Einschränkungen

1. **Smart-Mode-Phasenautomatik:** Smart Mode selbst wurde erfolgreich aktiviert. Die automatische 1↔3-Phasenumschaltung bei geeignetem PV-Überschuss ist noch nicht abschließend live bestätigt.
2. **OBC „2-phasig“:** Der Wert wird von AlphaESS-App und Portal gespeichert. In einem Live-Test mit einem Peugeot e-208 wurde trotz Auswahl „2-phasig“ extern auf allen drei Phasen Leistung gemessen. Die Entität ist deshalb eine **OBC-Sollwahl**, keine Messung der tatsächlich aktiven Phasen.
3. **STOP-Zuverlässigkeit:** Start und Stop funktionieren im manuellen Modus. In einem Test musste STOP einmal ein zweites Mal gesendet werden. Die Beta wiederholt STOP absichtlich **nicht automatisch**, solange die Ursache nicht reproduzierbar geklärt ist.
4. **`chargingAmount`:** Wird entsprechend der AlphaESS-App als **„In dieser Sitzung geladen“** angezeigt. Der Wert blieb im Test nach erneutem Anstecken erhalten; die genaue AlphaESS-Definition bzw. der Reset-Zeitpunkt ist noch offen.
5. **`lastChargingAmount`:** Wird als **„Letzter Ladeabschnitt“** angezeigt. Der Wert kann zeitweise `null` sein und erhält bewusst keinen künstlichen Fallback.
6. **„Heute laut Ladebericht“:** Separate Summe abgeschlossener Berichtseinträge des aktuellen Tages. In einem Test war der Wert trotz Live-Ladung noch 0,00 kWh; daher vorerst nur als experimentellen Berichtswert betrachten.

## Installation / Update

1. Vorhandenen Ordner `config/custom_components/alphaess_portal_bridge` sichern.
2. Aus dem ZIP den Ordner `custom_components/alphaess_portal_bridge` nach `config/custom_components/` kopieren und die vorhandenen Dateien ersetzen.
3. Home Assistant vollständig neu starten.
4. Eine bereits eingerichtete Integration **nicht löschen**. Zugangsdaten und Wallbox-Seriennummer bleiben im vorhandenen Config Entry erhalten.
5. Auf der Geräteseite unter Diagnose prüfen, welches **Portal-Profil** (`g1T` oder `g2T`) erkannt wurde.

Bei einer Neuinstallation wird die Integration wie gewohnt über **Einstellungen → Geräte & Dienste → Integration hinzufügen** eingerichtet.

## Polling

- Wallbox-/Konfigurationsdaten: ca. alle **30 Sekunden**
- Energiebericht: gecacht und höchstens etwa alle **5 Minuten** neu abgefragt

Kurze Übergangszustände der Wallbox können deshalb zwischen zwei Abfragen liegen und in Home Assistant nicht sichtbar werden.

## G2T-Zuordnungen

| Portal-Feld | Bedeutung |
|---|---|
| `chargeStrategy` | `0` Manuell, `1` Zeitgesteuert, `2` Plug and Play |
| `chargeMode` | `1` Langsam, `2` Schon, `3` Schnell, `4` Kundenspezifisch |
| `chargeCurrent` | kundenspezifischer Ladestrom, 6–16 A |
| `obcPhase` | OBC-Sollwahl 1 / 2 / 3 |
| `smartMode` | Smart Mode |
| `timePeriods` | bis zu drei Zeitrahmen |
| `houseHoldCurrent` | Hausstrom-Einstellung |
| `allowInstallersControl` | Installateursteuerung erlaubt |
| `gunLineSelfLockEnable` | Kabel-Selbstverriegelung |

## Beta-Feedback

Für einen Fehlerbericht sind besonders hilfreich:

- Home-Assistant-Version
- Wallbox-Modell sowie Hardware-/Software-Version
- erkanntes Portal-Profil `g1T` oder `g2T`
- Fahrzeugmodell, falls das Verhalten während einer Ladung auftritt
- genaue Ausgangseinstellung und ausgeführte Aktion
- beobachteter Status / Leistung vor und nach der Aktion
- relevante Home-Assistant-Logs

Bitte Zugangsdaten, Tokens und persönliche Daten aus Logs entfernen. Seriennummern können für öffentliche Beiträge ebenfalls geschwärzt werden.

Siehe außerdem `BETA_NOTES.md`, `CHANGELOG.md` und `NOTICE.md`.
