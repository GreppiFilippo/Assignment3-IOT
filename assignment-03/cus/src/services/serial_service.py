import asyncio
import json
import serial
import time
from typing import Optional
from pubsub import pub
from .base_service import BaseService
from utils.logger import get_logger

logger = get_logger(__name__)

class SerialService(BaseService):
    """
    Servizio Seriale completo:
    - Ascolta i cambiamenti di stato dal Controller (Pub/Sub).
    - Invia l'ultimo stato noto ad Arduino a intervalli regolari (Loop).
    - Legge i dati in arrivo da Arduino e li pubblica nel sistema.
    """

    def __init__(self, port: str, baudrate: int, send_interval: float = 0.5):
        super().__init__("serial_service")
        self.port = port
        self.baudrate = baudrate
        self._send_interval = send_interval
        
        # Stato del dispositivo (quello che Arduino deve sapere)
        self._current_state: dict = {}
        self._last_send_time = 0.0
        
        # Risorse hardware
        self._serial: Optional[serial.Serial] = None
        self._read_buffer = ""

    def subscribe_topics(self):
        """Si iscrive al topic per ricevere aggiornamenti dal Controller."""
        # Il controller invierà: pub.sendMessage("serial.update_state", data={"key": "val"})
        pub.subscribe(self._on_controller_update, "serial.update_state")

    def _on_controller_update(self, data: dict):
        """Callback eseguita quando il Controller pubblica un nuovo stato."""
        if isinstance(data, dict):
            self._current_state.update(data)
            logger.debug(f"[{self.name}] Stato aggiornato internamente: {self._current_state}")
        else:
            logger.warning(f"[{self.name}] Ricevuti dati non validi dal Controller: {data}")

    async def setup(self):
        """Apertura della porta seriale in modalità non bloccante."""
        try:
            loop = asyncio.get_running_loop()
            # L'apertura fisica della porta è un'operazione bloccante: usiamo l'executor
            self._serial = await loop.run_in_executor(
                None, 
                lambda: serial.Serial(
                    port=self.port, 
                    baudrate=self.baudrate, 
                    timeout=0.1,
                    write_timeout=0.1
                )
            )
            logger.info(f"[{self.name}] Connesso alla porta {self.port} ({self.baudrate} baud).")
        except Exception as e:
            logger.error(f"[{self.name}] Impossibile aprire la porta {self.port}: {e}")
            self._serial = None

    async def run(self):
        """Ciclo principale di invio e ricezione."""
        while self._running:
            # Se la seriale non è pronta, attendiamo e riproviamo
            if self._serial is None or not self._serial.is_open:
                await asyncio.sleep(2)
                # Qui potresti chiamare di nuovo setup() per tentare la riconnessione
                continue

            try:
                # 1. RICEZIONE: Legge i dati da Arduino
                await self._read_from_serial()

                # 2. INVIO PERIODICO: Invia lo stato ad Arduino ogni 'send_interval'
                current_time = time.monotonic()
                if current_time - self._last_send_time >= self._send_interval:
                    await self._send_to_serial(self._current_state)
                    self._last_send_time = current_time

            except Exception as e:
                logger.error(f"[{self.name}] Errore critico nel ciclo run: {e}")
                # Se l'errore è grave (es. cavo staccato), resettiamo la seriale
                if "device" in str(e).lower() or "io" in str(e).lower():
                    self._serial = None

            await asyncio.sleep(0.01) # Impedisce la saturazione della CPU

    async def _read_from_serial(self):
        """Gestisce la lettura asincrona dei dati in entrata."""
        if self._serial is None: return
        
        loop = asyncio.get_running_loop()
        ser = self._serial # Riferimento locale per evitare problemi di Type Checking
        
        try:
            # Controlla quanti byte sono nel buffer hardware
            waiting = await loop.run_in_executor(None, lambda: ser.in_waiting)
            
            if waiting > 0:
                raw_data = await loop.run_in_executor(None, lambda: ser.read(waiting))
                self._read_buffer += raw_data.decode('utf-8', errors='ignore')
                
                # Elabora le linee complete nel buffer
                while '\n' in self._read_buffer:
                    line, self._read_buffer = self._read_buffer.split('\n', 1)
                    await self._handle_incoming_json(line.strip())
        except Exception as e:
            logger.error(f"[{self.name}] Errore lettura seriale: {e}")
            self._serial = None

    async def _handle_incoming_json(self, line: str):
        """Decodifica il messaggio da Arduino e lo pubblica sul bus interno."""
        if not line: return
        try:
            data = json.loads(line)
            # Notifica il resto del sistema (es. il Controller o un Database)
            pub.sendMessage("serial.data_received", payload=data)
            logger.debug(f"[{self.name}] <== Ricevuto da Arduino: {data}")
        except json.JSONDecodeError:
            logger.warning(f"[{self.name}] Stringa non JSON ricevuta: {line}")

    async def _send_to_serial(self, data: dict):
        """Invia fisicamente il pacchetto JSON ad Arduino."""
        if self._serial is None: return
        
        try:
            loop = asyncio.get_running_loop()
            ser = self._serial
            # Arduino si aspetta spesso un terminatore di riga \n
            payload = (json.dumps(data) + '\n').encode('utf-8')
            
            await loop.run_in_executor(None, lambda: ser.write(payload))
            await loop.run_in_executor(None, ser.flush)
            logger.debug(f"[{self.name}] ==> Inviato ad Arduino: {data}")
        except Exception as e:
            logger.error(f"[{self.name}] Errore scrittura seriale: {e}")
            self._serial = None

    async def cleanup(self):
        """Chiude le risorse prima dello spegnimento."""
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
                logger.info(f"[{self.name}] Porta seriale chiusa correttamente.")
            except:
                pass
        self._serial = None