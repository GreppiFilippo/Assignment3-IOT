from models import SystemModel
import config
from src.services.event_bus import EventBus
import asyncio

class Orchestrator:
    def __init__(self):
        self.model = SystemModel()

    def _run(self):
        while True:
            # Aspetta l'intervallo desiderato
            asyncio.sleep(0.5)
            EventBus.publish(config.MODE, mode=self.model.mode)
            EventBus.publish(config.OPENING, opening=self.model.valve_opening)

    def handle_req_opening(self, opening):
        self.model.valve_opening = opening

    def handle_mode_change(self):
        if self.model.mode == "AUTOMATIC":
            self.model.mode = "MANUAL"
        elif self.model.mode == "MANUAL":
            self.model.mode = "AUTOMATIC"   
        else:
            return

    def handle_new_measurement(self, payload):
        self.model.add_level_reading(payload)
        EventBus.publish(config.LEVEL_OUT_TOPIC, self.model.get_readings())