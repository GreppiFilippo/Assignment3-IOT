from pubsub import pub
from typing import Callable
from utils.logger import get_logger

logger = get_logger(__name__)

class EventBus:
    """
    Wrapper intorno a PyPubSub che nasconde l'implementazione specifica.
    Gestisce la comunicazione tra Infrastructure Layer e Core Domain.
    """

    @staticmethod
    def publish(topic: str, **kwargs):
        """
        Invia un evento nel sistema.
        :param topic: Stringa identificativa (es. 'POT_VAL', 'VALVE_CMD')
        :param kwargs: Dati associati all'evento
        """
        try:
            # Nascondiamo la chiamata sendMessage di pypubsub
            pub.sendMessage(topic, **kwargs)
            logger.debug(f"[Bus] Publicato topic: {topic} con dati: {kwargs}")
        except Exception as e:
            logger.error(f"[Bus] Errore durante la pubblicazione su {topic}: {e}")

    @staticmethod
    def subscribe(topic: str, callback: Callable):
        """
        Registra un listener per un determinato topic.
        :param topic: Il tipo di evento da ascoltare
        :param callback: La funzione da eseguire al ricevimento dell'evento
        """
        try:
            pub.subscribe(callback, topic)
            logger.info(f"[Bus] Sottoscrizione registrata per topic: {topic}")
        except Exception as e:
            logger.error(f"[Bus] Errore durante la sottoscrizione a {topic}: {e}")