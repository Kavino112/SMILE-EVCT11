# Beta Notes – 0.5.2

## Zweck dieser Beta

Dies ist die erste öffentliche Beta des Storion4you-Community-Builds mit G2T-Unterstützung für die AlphaESS SMILE-G3-EVCT11/S.

Der Schwerpunkt der Beta ist nicht mehr die grundlegende Feldzuordnung, sondern der Test mit weiteren Kombinationen aus Wallbox-Firmware, Fahrzeugen und AlphaESS-Portalkonfigurationen.

## Besonders erwünschte Tests

- G2T mit anderen Fahrzeugen
- G2T mit anderen Hardware-/Softwareständen
- G1T-Regressionsprüfung
- Smart Mode bei realem PV-Überschuss und automatischer 1↔3-Phasenumschaltung
- Verhalten der OBC-Auswahl „2-phasig“ mit Fahrzeugen, die zweiphasiges AC-Laden unterstützen
- wiederholtes START/STOP im manuellen Modus
- Reset-/Fortschreibungsverhalten von `chargingAmount` über Tageswechsel und neue Steckvorgänge
- Plausibilität von „Heute laut Ladebericht“

## Bitte beachten

- G2T START/STOP ist absichtlich nur in **Manuell** freigegeben.
- Die Beta sendet **keinen automatischen zweiten STOP-Befehl**.
- „OBC-Phasenwahl“ ist eine Sollvorgabe und kein Sensor für tatsächlich stromführende Phasen.
- Bei Zeitrahmen sind nur Minuten `00`, `15`, `30` und `45` zulässig.

Bei unerwartetem Verhalten zuerst die AlphaESS-App bzw. das Portal prüfen und die Wallbox nicht durch schnelle wiederholte Schreibbefehle belasten.
