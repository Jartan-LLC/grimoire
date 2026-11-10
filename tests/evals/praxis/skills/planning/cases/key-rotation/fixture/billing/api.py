from billing.crypto import decrypt, encrypt


def customer_tax_id(row):
    return decrypt(row["tax_id_enc"])


def set_tax_id(conn, customer_id, tax_id):
    conn.execute("UPDATE customers SET tax_id_enc = %s WHERE id = %s",
                 (encrypt(tax_id), customer_id))
