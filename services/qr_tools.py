import io
import math
import uuid
import base64
import hashlib
import json

import qrcode
from qrcode.constants import ERROR_CORRECT_Q
from PIL import Image, ImageDraw, ImageFont
from pyzbar.pyzbar import decode as decode_qr
from cryptography.fernet import Fernet, InvalidToken


# -------- Helpers -------- #

def chunk_text(text, size: int):
    if size <= 0:
        raise ValueError("chunk_size must be positive")
    return [text[i:i+size] for i in range(0, len(text), size)]


def make_qr_image(data: str):
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_Q,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img.convert("RGB")


def add_index_label(img: Image.Image, index: int, total: int) -> Image.Image:
    """Add 'index/total' label below QR without touching the code area."""
    w, h = img.size
    label_height = max(24, h // 6)

    new_img = Image.new("RGB", (w, h + label_height), "white")
    new_img.paste(img, (0, 0))

    draw = ImageDraw.Draw(new_img)
    text = f"{index + 1}/{total}"

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    # Pillow 10+ uses textbbox instead of textsize
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (w - text_w) // 2
    y = h + (label_height - text_h) // 2

    draw.text((x, y), text, fill="black", font=font)
    return new_img


def tile_images(images):
    if not images:
        raise ValueError("No images to tile")

    widths, heights = zip(*(img.size for img in images))
    max_w, max_h = max(widths), max(heights)

    n = len(images)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    big_w = cols * max_w
    big_h = rows * max_h
    canvas = Image.new("RGB", (big_w, big_h), "white")

    for i, img in enumerate(images):
        r, c = divmod(i, cols)
        canvas.paste(img, (c * max_w, r * max_h))

    return canvas


# -------- Encryption helpers -------- #

def _get_fernet(passphrase: str) -> Fernet:
    """Derive a Fernet key from a passphrase using SHA-256."""
    key = hashlib.sha256(passphrase.encode("utf-8")).digest()
    key_b64 = base64.urlsafe_b64encode(key)
    return Fernet(key_b64)


def maybe_encrypt(text: str, passphrase: str | None) -> str:
    if not passphrase:
        return text
    f = _get_fernet(passphrase)
    cipher_bytes = f.encrypt(text.encode("utf-8"))
    return cipher_bytes.decode("utf-8")  # fernet outputs url-safe base64 bytes


def maybe_decrypt(text: str, passphrase: str | None):
    """Return (plaintext, error_str_or_None)."""
    if not passphrase:
        return text, None
    f = _get_fernet(passphrase)
    try:
        plain_bytes = f.decrypt(text.encode("utf-8"))
        return plain_bytes.decode("utf-8"), None
    except InvalidToken:
        return None, "Decryption failed. Wrong passphrase or corrupted data."


# -------- Checksum helpers -------- #

def wrap_payload_with_checksum(text: str) -> str:
    """
    Wrap the cleartext in a JSON object that includes its SHA-256 checksum.
    {
      "hash": "<hex>",
      "text": "<original_text>"
    }
    """
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    obj = {"hash": sha, "text": text}
    # ensure_ascii=False to preserve any unicode text
    return json.dumps(obj, ensure_ascii=False)


def unwrap_and_verify_payload(payload: str):
    """
    Given decrypted (or plain) payload, try to interpret it as our JSON wrapper:
      { "hash": "<sha256>", "text": "<original_text>" }

    If it's NOT valid JSON of that shape, we treat the payload as plain text
    with no checksum, and DO NOT raise an error.
    """
    try:
        obj = json.loads(payload)
    except Exception:
        # Not JSON → treat as legacy/plain text
        return payload, None, None

    if not isinstance(obj, dict):
        # Also treat as plain text if it's not an object
        return payload, None, None

    sha_stored = obj.get("hash")
    text = obj.get("text")

    # If fields not present → treat as plain text
    if not isinstance(sha_stored, str) or not isinstance(text, str):
        return payload, None, None

    sha_calc = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if sha_calc != sha_stored:
        return None, sha_stored, "Integrity check failed (SHA-256 mismatch)"

    return text, sha_stored, None


# -------- Encode -------- #

def _build_big_qr_image(payload: str, chunk_size: int, add_labels: bool = True) -> Image.Image:
    chunks = chunk_text(payload, chunk_size)
    msg_id = uuid.uuid4().hex[:8]
    total = len(chunks)

    images = []
    for idx, chunk in enumerate(chunks):
        encoded = f"{msg_id}|{idx}|{total}|{chunk}"
        img = make_qr_image(encoded)
        if add_labels:
            img = add_index_label(img, idx, total)
        images.append(img)

    return tile_images(images)


def encode_text_to_big_qr(text: str, chunk_size: int = 500, passphrase: str | None = None) -> str:
    """
    Returns base64 PNG string for embedding in HTML.
    Wraps the text with checksum, then (optionally) encrypts, then chunks.
    """
    wrapped = wrap_payload_with_checksum(text)
    payload = maybe_encrypt(wrapped, passphrase)
    big_img = _build_big_qr_image(payload, chunk_size, add_labels=True)

    buf = io.BytesIO()
    big_img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def encode_text_to_big_qr_file(text: str, chunk_size: int = 500, passphrase: str | None = None) -> io.BytesIO:
    """
    Returns BytesIO with PNG content for download / API.
    """
    wrapped = wrap_payload_with_checksum(text)
    payload = maybe_encrypt(wrapped, passphrase)
    big_img = _build_big_qr_image(payload, chunk_size, add_labels=True)

    buf = io.BytesIO()
    big_img.save(buf, format="PNG")
    buf.seek(0)
    return buf


# -------- Decode -------- #

def _decode_big_image(img: Image.Image):
    decoded = decode_qr(img)
    if not decoded:
        return None, "No QR codes found."

    messages = {}

    for symbol in decoded:
        try:
            content = symbol.data.decode("utf-8")
            parts = content.split("|", 3)
            if len(parts) != 4:
                continue
            msg_id, idx_str, total_str, chunk = parts
            idx = int(idx_str)
            total = int(total_str)

            if msg_id not in messages:
                messages[msg_id] = {"total": total, "parts": {}}

            messages[msg_id]["parts"][idx] = chunk
        except Exception:
            continue

    if not messages:
        return None, "Invalid QR format."

    msg_id, data = next(iter(messages.items()))
    total = data["total"]
    parts = data["parts"]

    missing = [i for i in range(total) if i not in parts]
    if missing:
        return None, f"Missing QR chunks: {missing}"

    payload = "".join(parts[i] for i in range(total))
    return payload, None


def decode_big_qr_to_text(file_stream, passphrase: str | None = None):
    """
    file_stream: Werkzeug FileStorage or file-like
    Returns (text, sha256_hex, error).
    """
    try:
        img = Image.open(file_stream).convert("RGB")
    except Exception as e:
        return None, None, f"Invalid image: {e}"

    payload, err = _decode_big_image(img)
    if err:
        return None, None, err

    wrapped, dec_err = maybe_decrypt(payload, passphrase)
    if dec_err:
        # Wrong passphrase (or corrupted encrypted data)
        return None, None, dec_err

    text, sha_hex, verify_err = unwrap_and_verify_payload(wrapped)
    if verify_err:
        # Only real error left is integrity mismatch on JSON-wrapped payload
        return None, sha_hex, verify_err

    # Debug (optional)
    print("decoded_len =", len(text))
    if sha_hex:
        print("sha256 =", sha_hex)

    return text, sha_hex, None

