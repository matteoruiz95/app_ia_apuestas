import hashlib
import getpass

password = getpass.getpass("Escribe la contraseña para generar SHA256: ")
print(hashlib.sha256(password.encode("utf-8")).hexdigest())
