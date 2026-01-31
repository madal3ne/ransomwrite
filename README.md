## ransomwrite

A simple Flask app to build "ransom-note" style text from scanned letter images.

Quick start (development):

1. Create and activate a virtual environment (recommended):

   python -m venv venv
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1

2. Install dependencies:

   pip install -r requirements.txt

3. Install the Tesseract binary (required for OCR):
   - Windows (UB-Mannheim): https://github.com/UB-Mannheim/tesseract/wiki
   - macOS: brew install tesseract
   - Linux (Debian/Ubuntu): sudo apt install tesseract-ocr

4. Start the app:

   python app.py

5. Open http://127.0.0.1:5000/

Docker (production-ish):

1. Build image:
   docker build -t ransomwrite .
2. Run with docker-compose (dev):
   docker-compose up --build

Configuration via environment variables:

- SECRET_KEY: Flask secret (default: dev-secret)
- TESSERACT_CMD: full path to tesseract binary (optional)
- MAX_CONTENT_LENGTH: request max size (bytes)
- ITEM_MAX_CHARS: maximum characters allowed per input (default 200)
- PORT: port for app to listen on (defaults to 5000)
- DEFAULT_RATE_LIMIT / API_RENDER_LIMIT / EXPORT_LIMIT: rate limit strings (e.g. "30 per minute")

CI:
- GitHub Actions runs tests on push to `main` (see `.github/workflows/ci.yml`).

Running tests locally:

- Create and activate a virtual environment (recommended):

  python -m venv .venv
  # Windows PowerShell
  .\.venv\Scripts\Activate.ps1

- Install dependencies:

  pip install -r requirements.txt

- Ensure the Tesseract binary is installed and accessible (see above).

- Run the test suite:

  python -m pytest -q

Notes:
- If `pytest` is not on your PATH, use `python -m pytest` to run the test runner. 
- Set `TESSERACT_CMD` in your environment if Tesseract is installed in a custom location.

