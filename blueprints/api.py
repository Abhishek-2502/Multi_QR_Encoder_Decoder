from flask import Blueprint, request, jsonify, send_file
from services.qr_tools import encode_text_to_big_qr_file, decode_big_qr_to_text

api_bp = Blueprint("api", __name__)


@api_bp.route("/encode", methods=["POST"])
def encode_api():
    payload = request.get_json(silent=True) or {}
    data = payload.get("data")
    chunk_size = int(payload.get("chunk_size", 500))
    passphrase = payload.get("passphrase") or None

    if not data:
        return jsonify({"error": "Provide 'data' in JSON body."}), 400

    try:
        buf = encode_text_to_big_qr_file(data, chunk_size, passphrase=passphrase)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return send_file(
        buf,
        mimetype="image/png",
        as_attachment=True,
        download_name="multi_qr.png",
    )


@api_bp.route("/decode", methods=["POST"])
def decode_api():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded (key 'file')"}), 400

    file = request.files["file"]
    passphrase = request.form.get("passphrase") or request.args.get("passphrase")
    if passphrase:
        passphrase = passphrase.strip()

    text, sha_hex, err = decode_big_qr_to_text(file, passphrase=passphrase)
    if err:
        return jsonify({"error": err, "sha256": sha_hex}), 400

    return jsonify({"data": text, "sha256": sha_hex})
