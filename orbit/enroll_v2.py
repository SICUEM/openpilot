"""Constantes y funciones puras de la vinculacion segura (enroll v2).

Solo stdlib. El backend reproduce el mismo hash; un vector de prueba fijo lo comprueba.
"""
import hashlib
import secrets

ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # 32 simbolos = 5 bits, sin ambiguos
LONGITUD = 26                                    # 26*5 = 130 bits >= 128
PREFIJO = "orbit-enroll-v2"


def nuevo_token() -> str:
  return "".join(secrets.choice(ALFABETO) for _ in range(LONGITUD))


def normalizar_codigo(texto) -> str:
  return "".join(c for c in str(texto).strip().upper() if c not in " -\t")


def hash_enrolamiento(dongle_id: str, token: str, pubkey_pem: str) -> str:
  # pubkey_pem: la cadena EXACTA que viaja en el campo `pubkey` del enroll.
  return hashlib.sha256(f"{PREFIJO}|{dongle_id}|{token}|{pubkey_pem}".encode()).hexdigest()


def url_enrolamiento(dongle_id, codigo) -> str:
  return f"orbit://enroll?d={dongle_id}&c={codigo}" + ("&v=2" if len(codigo) == LONGITUD else "")


def codigo_legible(token) -> str:
  return " ".join(token[i:i + 4] for i in range(0, len(token), 4))
