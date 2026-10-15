"""
can_manager.py
Classe CanManager : encapsule la communication CAN (python-can / SocketCAN).
Le reste de l'application n'a pas besoin de connaître python-can.
"""

import can


class CanManager:
    """Gère l'ouverture, l'envoi, la réception et la fermeture du bus CAN."""

    def __init__(self, channel="can0", bitrate=500000):
        self.channel = channel
        self.bitrate = bitrate      # informatif : le bitrate est configuré par "ip link"
        self.bus = None

    # ------------------------------------------------------------------
    # Ouverture / fermeture
    # ------------------------------------------------------------------
    def open(self):
        """Ouvre l'interface SocketCAN. Retourne True si succès."""
        if self.bus is not None:
            return True
        try:
            self.bus = can.interface.Bus(channel=self.channel, interface="socketcan")
            return True
        except (can.CanError, OSError) as e:
            print(f"[CanManager] Erreur ouverture {self.channel} : {e}")
            self.bus = None
            return False

    def close(self):
        """Ferme proprement l'interface CAN."""
        if self.bus is not None:
            self.bus.shutdown()
            self.bus = None

    # Permet d'utiliser : with CanManager() as can_mgr:
    def __enter__(self):
        if not self.open():
            raise RuntimeError(f"Impossible d'ouvrir {self.channel}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    # ------------------------------------------------------------------
    # Envoi
    # ------------------------------------------------------------------
    def send(self, can_id, data):
        """
        Envoie une trame CAN standard (11 bits).
        can_id : identifiant (ex. 0x100)
        data   : liste ou bytes de 0 à 8 octets
        Retourne True si la trame a été envoyée.
        """
        if self.bus is None:
            print("[CanManager] Bus non ouvert")
            return False
        try:
            msg = can.Message(
                arbitration_id=can_id,
                data=bytes(data),
                is_extended_id=False,
            )
            self.bus.send(msg)
            return True
        except (can.CanError, ValueError) as e:
            print(f"[CanManager] Erreur envoi : {e}")
            return False

    # ------------------------------------------------------------------
    # Réception
    # ------------------------------------------------------------------
    def receive(self, timeout=1.0):
        """
        Attend une trame CAN pendant 'timeout' secondes.
        Retourne un can.Message, ou None si rien n'est reçu.
        """
        if self.bus is None:
            print("[CanManager] Bus non ouvert")
            return None
        try:
            return self.bus.recv(timeout)
        except can.CanError as e:
            print(f"[CanManager] Erreur réception : {e}")
            return None

    def receive_id(self, expected_id, timeout=1.0):
        """
        Attend une trame ayant un identifiant précis (ignore les autres).
        Retourne le can.Message, ou None si le délai expire.
        """
        import time
        fin = time.monotonic() + timeout
        while True:
            restant = fin - time.monotonic()
            if restant <= 0:
                return None
            msg = self.receive(restant)
            if msg is None:
                return None
            if msg.arbitration_id == expected_id:
                return msg