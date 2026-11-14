import os

from cryptography.fernet import Fernet

_fernet = Fernet(os.environ["TAX_ID_KEY"])


def encrypt(tax_id):
    return _fernet.encrypt(tax_id.encode()).decode()


def decrypt(token):
    return _fernet.decrypt(token.encode()).decode()
