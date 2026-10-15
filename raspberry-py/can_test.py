"""
can_test.py
Séquence de test automatique de la communication CAN avec le STM32 périphérique.

Séquence :
  1. LED ON  (0x100, DB0=0x01)  -> ACK attendu (0x210)
  2. LED OFF (0x100, DB0=0x00)  -> ACK attendu (0x210)
  3. Demande de valeur (0x101)  -> réponse attendue (0x201, uint16 sur 2 octets)
"""

import time
from can_manager import CanManager

# ----------------------------------------------------------------------
# Identifiants CAN du protocole
# ----------------------------------------------------------------------
ID_CMD_LED = 0x100   # commande LED (DB0 : 1 = ON, 0 = OFF)
ID_REQ_VAL = 0x101   # demande de valeur
ID_ACK     = 0x210   # accusé de réception
ID_VAL     = 0x201   # réponse contenant la valeur uint16

TIMEOUT_S = 1.0      # délai d'attente d'une réponse (secondes)


def envoyer_led(can_mgr, etat):
    """Envoie la commande LED et attend l'ACK. Retourne True si ACK=1 reçu."""
    texte = "ON" if etat else "OFF"
    print(f"TX : commande LED {texte}")
    if not can_mgr.send(ID_CMD_LED, [1 if etat else 0]):
        print("Erreur : envoi impossible")
        return False

    ack = can_mgr.receive_id(ID_ACK, TIMEOUT_S)
    if ack is None:
        print(f"RX : aucun ACK reçu (timeout {TIMEOUT_S} s)")
        return False

    valeur_ack = ack.data[0] if len(ack.data) > 0 else 0
    print(f"RX : 0x{ack.arbitration_id:03X} ACK={valeur_ack}")
    return valeur_ack == 1


def demander_valeur(can_mgr):
    """Demande la valeur au STM32 et reconstruit le uint16. Retourne la valeur ou None."""
    print("TX : demande compteur")
    if not can_mgr.send(ID_REQ_VAL, []):
        print("Erreur : envoi impossible")
        return None

    rep = can_mgr.receive_id(ID_VAL, TIMEOUT_S)
    if rep is None:
        print(f"RX : aucune réponse reçue (timeout {TIMEOUT_S} s)")
        return None

    if len(rep.data) < 2:
        print(f"RX : trame trop courte (DLC={len(rep.data)})")
        return None

    print(f"RX : 0x{rep.arbitration_id:03X}  DB0=0x{rep.data[0]:02X}  DB1=0x{rep.data[1]:02X}")

    # Reconstruction du uint16 : octet de poids fort en premier
    valeur = (rep.data[0] << 8) | rep.data[1]
    return valeur


def main():
    try:
        with CanManager("can0") as can_mgr:
            ok_on = envoyer_led(can_mgr, True)
            time.sleep(1)

            ok_off = envoyer_led(can_mgr, False)
            time.sleep(0.5)

            valeur = demander_valeur(can_mgr)
            if valeur is not None:
                print(f"Valeur : {valeur}")

            print("\n--- Résumé ---")
            print(f"LED ON  : {'OK' if ok_on else 'ECHEC'}")
            print(f"LED OFF : {'OK' if ok_off else 'ECHEC'}")
            print(f"Valeur  : {valeur if valeur is not None else 'ECHEC'}")

    except RuntimeError as e:
        print(f"Erreur : {e}")
        print("Vérifiez que can0 est actif : ip -details link show can0")


if __name__ == "__main__":
    main()