from cryptography.fernet import Fernet

encryption_key = Fernet.generate_key()

print("Your encryption key:", encryption_key.decode())

with open("encryption_key.txt", "w") as key_file:
    key_file.write(encryption_key.decode())
