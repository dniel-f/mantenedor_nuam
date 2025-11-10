import bcrypt
import getpass

# Pide la contraseña de forma segura (no la muestra en pantalla)
password = getpass.getpass("Escribe la nueva contraseña segura para el admin: ")

# Codificar la contraseña a bytes
password_bytes = password.encode('utf-8')

# Generar el 'salt' y crear el hash
salt = bcrypt.gensalt()
hash_bytes = bcrypt.hashpw(password_bytes, salt)

# Decodificar el hash para guardarlo como string en la BBDD
hash_string = hash_bytes.decode('utf-8')

print("\n--- ¡Hash generado! ---")
print("Copia esta línea completa y pégala en tu consulta SQL:\n")
print(hash_string)