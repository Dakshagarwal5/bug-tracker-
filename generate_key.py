from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import os

private_key_path = 'keys/private.pem'
public_key_path = 'keys/public.pem'

if not os.path.exists(private_key_path):
    print(f"Error: {private_key_path} not found.")
    exit(1)

with open(private_key_path, "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
        backend=default_backend()
    )

public_key = private_key.public_key()

with open(public_key_path, "wb") as key_file:
    key_file.write(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )

print(f"Successfully generated {public_key_path}")
