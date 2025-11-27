# 🧩 Multi-QR Encoder & Decoder

**Multi-QR Encoder & Decoder** is a web app that lets you pack **large text payloads** into a single image made of multiple QR tiles – then decode it back later with **optional encryption** and **SHA-256 integrity checks**.

> 💡 Ideal for large text payloads: **15k–50k characters** (practically up to ~100k).

---

## 📚 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [How It Works](#how-it-works)
- [Getting Started](#getting-started)
- [Usage](#usage)
  - [Encoding Text → Big QR](#encoding-text--big-qr)
  - [Decoding Big QR → Text](#decoding-big-qr--text)
- [Project Structure](#project-structure)
- [Screenshots](#screenshots)
- [Limitations & Notes](#limitations--notes)
- [License](#license)
- [Author](#author)

---

## Overview

Standard QR codes have hard limits on how much data they can store. **Multi-QR Encoder & Decoder** solves this by:

- Splitting your text into multiple chunks
- Encoding each chunk as a separate QR tile
- Combining all tiles into **one large PNG image** with numbered tiles
- Later, decoding that same image back into the original text

To keep your data safe, the app supports **passphrase-based encryption** and verifies content integrity with **SHA-256** before displaying your text.

---

## Key Features

- ✅ **Large-Text Encoding**  
  Convert long text (tens of thousands of characters) into a composition of multiple QR codes in one image.

- 🔐 **Passphrase Encryption (Optional)**  
  Encrypt the payload with a passphrase using Fernet (AES under the hood) before chunking and encoding.

- 🧩 **Multi-QR Tiling**  
  Automatically splits your payload into chunks and generates an image grid of QR tiles, each labeled with its index (e.g., `1/8`, `2/8`, …).

- ✅ **SHA-256 Integrity Check**  
  The original text is wrapped with a SHA-256 hash. On decode, the app recomputes the hash and verifies it to detect corruption or tampering.

- 🧮 **Live Stats While Encoding**  
  Shows **character count** and **estimated number of QR tiles** based on your chosen chunk size.

- 📥 **Single-Image Download**  
  Download a single PNG that contains all QR tiles, ready to be stored, printed, or shared.

- 🚫 **No Login Required**  
  Use the app instantly without creating an account or signing in — just open, encode, and decode.

- 🎨 **Modern UI**  
  Tailwind CSS + subtle animations, sticky navbar, responsive layout, and a 3D spinning “QR cube” visual on the landing page.

---

## Tech Stack

### Backend

| Technology        | Purpose                                                                 |
|-------------------|-------------------------------------------------------------------------|
| **Python**        | Core programming language                                               |
| **Flask** (implied) | Web framework handling routes for encoding and decoding                |
| **qrcode**        | Generates individual QR code images                                    |
| **Pillow (PIL)**  | Image processing, compositing tiles, drawing labels                    |
| **pyzbar**        | Decoding QR codes from the combined image                              |
| **cryptography**  | Fernet encryption/decryption using a key derived from a passphrase     |
| **hashlib**       | SHA-256 hashing for integrity checking                                 |
| **uuid**          | Generates unique message IDs for grouping QR chunks                    |
| **Docker**          | For Containerized App                                                |

### Frontend

| Technology     | Purpose                                                   |
|----------------|-----------------------------------------------------------|
| **HTML + Jinja** | Server-rendered templates for the landing page and app UI |
| **Tailwind CSS** | Utility-first styling for layout, colors, and components |
| **Vanilla JS**   | Live character/tile stats, copy-to-clipboard, loader UX |

---

## How It Works

1. **User inputs text** on the app page.
2. The backend **wraps** the text in a JSON object:
   ```json
   {
     "hash": "<sha256-of-text>",
     "text": "<original_text>"
   }
3. If a passphrase is provided:

   * A Fernet key is derived from `SHA-256(passphrase)`.
   * The JSON payload is **encrypted**.
4. The final payload (plain or encrypted) is **chunked** into fixed-size pieces.
5. Each chunk becomes a QR payload with metadata:
   `msg_id | chunk_index | total_chunks | chunk_data`
6. Each QR code is generated and optionally labeled (`index/total`).
7. All labeled tiles are **tiled into a single PNG**.
8. On decode, the process reverses:

   * Detect all QR codes in the image.
   * Group them by `msg_id`, reassemble chunks in order.
   * Optionally **decrypt** using the passphrase.
   * Parse JSON wrapper and verify SHA-256 before returning text.

---

## Getting Started

### Prerequisites

* **Python 3.10+**
* **pip** (Python package manager)
* (Optional) A virtual environment tool (`venv`, `conda`, etc.)

### 1. Clone the Repository

```bash
git clone https://github.com/Abhishek-2502/Multi_QR_Encoder_Decoder
cd Multi_QR_Encoder_Decoder
```

### 2. Create & Activate Virtual Environment (Recommended)

```bash
python -m venv venv
# On Linux/macOS
source venv/bin/activate
# On Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the App

```bash
python app.py
```

By default, the app usually runs on:

```text
http://127.0.0.1:5000
```

* Landing page: `/`
* App page: `/app`

---

## Usage

### Encoding Text → Big QR

1. Open the **App** page (e.g., `http://127.0.0.1:5000/app`).
2. In the **Encode Text → Big QR** panel:

   * Paste or type your long text into **“Text to encode”**.
   * Optionally adjust **Chunk size (chars per QR)**:

     * Higher = fewer tiles but denser (harder to scan individually).
   * Optionally provide a **Passphrase** for encryption.
3. The UI will show:

   * `X characters`
   * `Estimated tiles: Y`
4. Click **“Generate Big QR”**.
5. Once processing finishes:

   * The combined QR PNG appears below.
   * Click **“⬇ Download PNG”** to save it.

### Decoding Big QR → Text

1. Go to the same **App** page.
2. In the **Decode Big QR → Text** panel:

   * **Upload the PNG** you previously generated.
   * If you used a passphrase while encoding, **enter the same passphrase**.
3. Click **“Decode Image”**.
4. If everything is valid, you will see:

   * The **decoded text** inside a scrollable box.
   * An **“Integrity: Verified”** badge if the SHA-256 check passes.
5. Use the **“Copy”** button to copy the decoded text to your clipboard.

If anything fails (missing chunks, wrong passphrase, hash mismatch), a clear error message is displayed.

---

## Project Structure

A layout for this app look like:

```bash
multi-qr-encoder-decoder/
├─ app.py                     # Flask entrypoint
├─ requirements.txt
├─ Dockerfile
├─ templates/
│  ├─ landing.html            # Landing page (3D QR cube, overview, etc.)
│  └─ app.html                # Encode/Decode UI with forms & results
└─ static/
   ├─ images/
   │  └─ favicon.ico
   └─ ...
```

## Screenshots

![alt text](<static/readme/Landing.png>)  
![alt text](<static/readme/Encode.png>)  
![alt text](<static/readme/Decode.png>)  
![alt text](<static/readme/Loader.png>)  

---

## Limitations & Notes

* 📏 **Payload size**
  
  Practical range is around **15k–50k characters**, with support up to roughly **100k characters**, depending on chunk size and environment.

* 📷 **Image Quality**
  
  If the combined PNG is resized, compressed, or heavily distorted, decoding may fail or chunks may go missing.

* 🔐 **Passphrase Safety**

  * The passphrase is never stored; if you forget it, the encrypted data cannot be recovered.
  * Wrong passphrases will cause decryption to fail.

* 🧪 **Single Message per Image**
  
  The current design decodes **one message ID** from the big image (all tiles belong to the same logical message).

---

## License

This project is licensed under the **MIT License**.
See the [`LICENSE`](./LICENSE) file for details.

---

## Author

**Abhishek Rajput**


