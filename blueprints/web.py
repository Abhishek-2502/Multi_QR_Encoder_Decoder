from flask import Blueprint, render_template, request
from services.qr_tools import encode_text_to_big_qr, decode_big_qr_to_text

web_bp = Blueprint("web", __name__)


@web_bp.route("/", methods=["GET"])
def landing():
    # Just render the landing/info page
    return render_template("landing.html")


@web_bp.route("/app", methods=["GET", "POST"])
def app_view():
    encoded_image_b64 = None
    decoded_text = None
    decoded_hash = None
    encode_error = None
    decode_error = None

    if request.method == "POST":
        mode = request.form.get("mode")

        if mode == "encode":
            text = request.form.get("data", "")
            chunk_size = int(request.form.get("chunk_size", "500") or "500")
            passphrase = request.form.get("passphrase", "").strip() or None

            if not text.strip():
                encode_error = "Please provide some text to encode."
            else:
                try:
                    encoded_image_b64 = encode_text_to_big_qr(
                        text,
                        chunk_size,
                        passphrase=passphrase
                    )
                except Exception as e:
                    encode_error = f"Failed to encode: {e}"

        elif mode == "decode":
            passphrase = request.form.get("passphrase", "").strip() or None
            file = request.files.get("file")
            if not file:
                decode_error = "Please upload a QR image."
            else:
                try:
                    decoded_text, decoded_hash, err = decode_big_qr_to_text(
                        file,
                        passphrase=passphrase
                    )
                    if err:
                        decode_error = err
                except Exception as e:
                    decode_error = f"Failed to decode: {e}"

    return render_template(
        "app.html",
        encoded_image=encoded_image_b64,
        decoded_text=decoded_text,
        decoded_hash=decoded_hash,
        encode_error=encode_error,
        decode_error=decode_error,
    )
