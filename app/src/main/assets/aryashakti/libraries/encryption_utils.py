import base64
import json
import hashlib
from django.conf import settings
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes



# Module-level constants for performance
if settings.AXIS_AES_KEY_HEX:
    _KEY = bytes.fromhex(settings.AXIS_AES_KEY_HEX)
    _IV = bytes([
        0x8E, 0x12, 0x39, 0x9C, 0x07, 0x72, 0x6F, 0x5A,
        0x8E, 0x12, 0x39, 0x9C, 0x07, 0x72, 0x6F, 0x5A
    ])


def aes_encrypt_base64(plaintext: bytes) -> str:
    """
    Encrypts plaintext using AES CBC PKCS7 and returns base64 string with IV prepended.
    """
    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()
    cipher = Cipher(algorithms.AES(_KEY), modes.CBC(_IV))
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(_IV + encrypted).decode()


def aes_decrypt_base64(ciphertext_b64: str) -> dict:
    """
    Decrypts base64-encoded AES CBC ciphertext (with IV prepended) to a JSON object.
    """
    encrypted_data = base64.b64decode(ciphertext_b64)
    iv = encrypted_data[:16]
    ct = encrypted_data[16:]

    cipher = Cipher(algorithms.AES(_KEY), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ct) + decryptor.finalize()

    unpadder = sym_padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
    decrypted_str = plaintext.decode("utf-8")

    try:
        return json.loads(decrypted_str)
    except json.JSONDecodeError:
        raise ValueError("[AxisBank] Decrypted response is not valid JSON.")


def validate_info(value):
    """
    Axis logic: Treat None/null as empty string in checksum generation.
    """
    return "" if value in [None, "null"] else str(value)


def flatten_and_concat(data):
    """
    Recursively flatten all string values for checksum input.
    """
    values = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "checksum":
                continue
            values.append(flatten_and_concat(value))
    elif isinstance(data, list):
        for item in data:
            values.append(flatten_and_concat(item))
    else:
        values.append(validate_info(data))
    return "".join(values)

def flatten_and_concat_str(data) -> str:
    """
    Flatten data into a single string for MD5, without list appends.
    """
    result = []

    def _flatten(value):
        if isinstance(value, dict):
            for k, v in value.items():
                if k == "checksum":
                    continue
                _flatten(v)
        elif isinstance(value, list):
            for item in value:
                _flatten(item)
        else:
            result.append("" if value in [None, "null"] else str(value))

    _flatten(data)
    return "".join(result)

def generate_md5_checksum(data_dict):
    """
    Generate MD5 checksum from flattened payload.
    """
    flat_string = flatten_and_concat_str(data_dict)
    if flat_string:
        return hashlib.md5(flat_string.encode("utf-8")).hexdigest()
    return ""


def prepare_encrypted_request(data_dict: dict) -> str:
    """
    Prepares AES-encrypted payload for Axis Bank request with checksum appended.
    """
    checksum = generate_md5_checksum(data_dict)
    data_dict["checksum"] = checksum

    json_body = json.dumps(data_dict, separators=(",", ":")).encode()
    encrypted_payload = aes_encrypt_base64(json_body)
    return encrypted_payload
