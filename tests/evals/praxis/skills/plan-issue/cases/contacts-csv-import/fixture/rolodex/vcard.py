"""Export contacts as vCard 3.0."""


def to_vcard(contact: dict[str, str]) -> str:
    """One contact as a vCard."""
    lines = ["BEGIN:VCARD", "VERSION:3.0", f"FN:{contact['name']}", f"EMAIL:{contact['email']}"]
    if contact["phone"]:
        lines.append(f"TEL:{contact['phone']}")
    lines.append("END:VCARD")
    return "\r\n".join(lines)
