from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import base64


def decrypt_aes_256_cbc(key, iv, ciphertext):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
    return decrypted_data


def encrypt_aes_256_cbc(key, iv, cleartext):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(cleartext.encode())
    padded_data += padder.finalize()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return ciphertext


key = "QtRGfLst9ABGMnMMUoB+zzTB9vI8Zwc06/VzsjW+YFM="[:32].encode()

decoded_bytes = base64.b64decode("3lqQCYxs7SvP93CuQX9sGjllVlA0cGxjWXdIS1NlWXUvOEZNMzRUTWxmWVkyY0VDcG1EUTdUaXZnSjNOb0RwWW9KTjNUUlJnOXMwR29rb1ByTThMVTNKTUJUUDA0UDJjY1dsMlFnPT0=")

iv = decoded_bytes[:16]
ciphertext = base64.b64decode(decoded_bytes[16:])

print(decrypt_aes_256_cbc(key, iv, ciphertext).decode())
print(base64.b64encode(iv + base64.b64encode(encrypt_aes_256_cbc(key, iv, "Ответ: 4"))))
