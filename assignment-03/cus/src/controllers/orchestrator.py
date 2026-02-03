from models import SystemModel
import config
from src.services.event_bus import EventBus

class Orchestrator:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.model = SystemModel()

    def handle_req_opening(self, request):
        self.model.valve_opening = request.get("valve_opening", 0.0)
        self.event_bus.publish(config.OPENING, )