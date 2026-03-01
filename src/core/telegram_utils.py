"""
Utilidades para el canal Telegram.
Portado desde legacy/src/core/telegram_utils.py con adaptaciones menores de estilo.
"""
import re

TELEGRAM_MAX_MESSAGE_LENGTH = 4096


def escape_html_for_telegram(text: str) -> str:
    """
    Escapa caracteres HTML inválidos (<, >) para evitar errores 400 en Telegram
    cuando se usa parse_mode='HTML', respetando las etiquetas válidas de Telegram.

    Etiquetas permitidas por Telegram: b, strong, i, em, u, ins, s, strike, del, a, code, pre.
    """
    if not text:
        return ""

    allowed_tags = ["b", "strong", "i", "em", "u", "ins", "s", "strike", "del", "a", "code", "pre"]

    # Expresión regular para coincidir con cualquier estructura que parezca etiqueta HTML
    pattern = re.compile(r"(</?[a-zA-Z0-9]+[^>]*>)")

    # split() con un grupo de captura devuelve las coincidencias intercaladas con el texto
    # Ej: "hola <b>mundo</b>!" → ["hola ", "<b>", "mundo", "</b>", "!"]
    parts = pattern.split(text)

    for i in range(len(parts)):
        if i % 2 == 1:
            # Índices impares son posibles etiquetas
            tag_name_match = re.match(r"</?([a-zA-Z0-9]+)", parts[i])
            if tag_name_match and tag_name_match.group(1).lower() in allowed_tags:
                continue  # Etiqueta permitida → dejar intacta
            else:
                parts[i] = parts[i].replace("<", "&lt;").replace(">", "&gt;")
        else:
            # Índices pares son texto normal fuera de etiquetas
            parts[i] = parts[i].replace("<", "&lt;").replace(">", "&gt;")

    return "".join(parts)


def chunk_telegram_message(text: str, max_length: int = TELEGRAM_MAX_MESSAGE_LENGTH) -> list[str]:
    """
    Divide un mensaje largo en partes donde ninguna excede max_length.
    Intenta dividir por saltos de línea para preservar el formato.
    """
    if not text:
        return []

    if len(text) <= max_length:
        return [text]

    chunks = []
    current_text = text

    while len(current_text) > max_length:
        # Buscar el último salto de línea dentro del límite
        split_index = current_text.rfind("\n", 0, max_length)

        # Si no hay saltos, buscar el último espacio
        if split_index == -1:
            split_index = current_text.rfind(" ", 0, max_length)

        # Si tampoco hay espacios, cortar exactamente en el límite
        if split_index == -1:
            split_index = max_length

        chunk = current_text[:split_index].strip()
        if chunk:
            chunks.append(chunk)

        current_text = current_text[split_index:].strip()

    if current_text:
        chunks.append(current_text)

    return chunks
