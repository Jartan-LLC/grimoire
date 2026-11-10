from billing.crypto import decrypt


def invoice_header(row):
    return {"customer": row["name"], "tax_id": decrypt(row["tax_id_enc"])}
