import secrets


def generate_access_token():

    return secrets.token_hex(16)