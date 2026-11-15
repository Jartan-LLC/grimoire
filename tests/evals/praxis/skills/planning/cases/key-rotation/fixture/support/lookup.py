from billing.crypto import decrypt


def show(row):
    print(row["name"], decrypt(row["tax_id_enc"]))
