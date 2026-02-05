cus -> wcs
    {"mode":"AUTO","valve":40}
wcs -> cus
    {"alive":true,"req_val":"40","btn":false}




# WCS - Water Channel Subsystem: Architettura e Scelte

## FSM
- La WCS implementa **una FSM minima** basata solo sulla **connettività con il CUS**:
  - `CONNECTED`
  - `UNCONNECTED`
- Transizioni:
  - `CONNECTED → UNCONNECTED` → timeout seriale / assenza messaggi dal CUS
  - `UNCONNECTED → CONNECTED` → ricezione di un JSON valido dal CUS
- Tutta la logica di policy (apertura valvola, modalità) resta **sul CUS**.

## Modalità AUTO / MANUAL
- **Non sono stati della FSM**.
- Sono trattate come **dati/configurazione ricevuti dal CUS**.
- Usate per:
  - decidere quali input locali leggere (pulsante, potenziometro)
  - aggiornare il display LCD
- La WCS non prende decisioni autonome basate su AUTO/MANUAL.

## Comunicazione CUS ↔ WCS
- Il CUS invia **sempre lo stato completo** in JSON:
```json
{
  "mode": "AUTO" | "MANUAL",
  "valve": 0-100
}
