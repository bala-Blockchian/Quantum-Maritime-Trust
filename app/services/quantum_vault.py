import oqs
import os

KEY_PATH = "../../keys/master_quantum.key"
ALG_NAME = "ML-DSA-65"

def get_or_create_master_key():
    if os.path.exists(KEY_PATH):
        with open(KEY_PATH, "rb") as f:
            print(f"Loaded Persistent {ALG_NAME} Master Key.")
            return f.read()
    else:
        with oqs.Signature(ALG_NAME) as signer:
            signer.generate_keypair()
            private_key = signer.export_secret_key()
            with open(KEY_PATH, "wb") as f:
                f.write(private_key)
            print(f"Generated and Saved New {ALG_NAME} Master Key.")
            return private_key

def sign_with_mldsa(data_hash: bytes):
    secret_key = get_or_create_master_key()
    
    with oqs.Signature(ALG_NAME, secret_key=secret_key) as signer:
        signature = signer.sign(data_hash)
        
        print(f"Document signed with {ALG_NAME} Master Key.")
        return signature, ALG_NAME