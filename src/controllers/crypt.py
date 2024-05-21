import base64
import json
import logging
import random

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from config import settings


def decrypt_aes_256_cbc(key, iv, ciphertext):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(decrypted_data)
    return data + unpadder.finalize()


def encrypt_aes_256_cbc(key, iv, cleartext):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(cleartext.encode())
    padded_data += padder.finalize()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return ciphertext


class Crypt:
    def __init__(self, encrypt_key: bytes, decrypt_key: bytes):
        self.encrypt_key = encrypt_key
        self.decrypt_key = decrypt_key

    def decrypt(self, message: str):
        decoded_bytes = base64.b64decode(message)
        iv = decoded_bytes[:16]
        ciphertext = base64.b64decode(decoded_bytes[16:])
        return decrypt_aes_256_cbc(self.decrypt_key, iv, ciphertext).decode()
        # return decrypt_aes_256_cbc(self.decrypt_key, iv, ciphertext).decode()

    def encrypt(self, message: str) -> str:
        iv = random.randbytes(16)
        return base64.b64encode(iv + base64.b64encode(encrypt_aes_256_cbc(self.encrypt_key, iv, message))).decode()


# a = Crypt(settings.key_encrypt, settings.key_decrypt)
# b = a.decrypt('3EcIMd8Xcg0wdZKP1NjkBVlDQmg5OTdlbTN5T21wUFNhM3RlaVRWbXJ3S1l2ZXpyc0dTQ01pRzArU0puMXF1QzFyNDRyL0tLL09CRkZ5Zkw4MlJOV2NvZzRmZlQ5TndwRkFPZWdjQlgzOWRXQlQrWUFvZDUvRmI5eWFBOXRGdEtNbWZjR1cvazE3RzU5YXFY')
# c = {'order_id': 2968, 'user_id': 2702, 'requisite': 'Senior Pomidoro', 'amount': '9.55', 'status': 0}
# print(b)



