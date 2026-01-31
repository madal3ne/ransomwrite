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

Render deployment & Docker tips:

- If you plan to deploy on Render (or another PaaS), note that **Tesseract is required** for OCR to work. The included `Dockerfile` installs `tesseract-ocr` so Docker-based deploys are the easiest way to ensure system dependencies are available.
- If you prefer Render's native build (no Dockerfile), add a build step to install Tesseract (Debian/Ubuntu example):

  apt-get update && apt-get install -y tesseract-ocr

Recommended Render environment variables:

- `SECRET_KEY` — secure secret for Flask sessions (set to a long random value)
- `TESSERACT_CMD` — path to the Tesseract binary (e.g., `/usr/bin/tesseract` in the container)
- `ITEM_MAX_CHARS` — max characters per input (default 200)
- `MAX_CONTENT_LENGTH` — max request size in bytes
- `DEFAULT_RATE_LIMIT`, `API_RENDER_LIMIT`, `EXPORT_LIMIT` — rate limits (e.g., `"30 per minute"`)
- `GUNICORN_WORKERS` — optional: number of Gunicorn workers to run

Tip: After the first deploy, check service logs for font or Tesseract path errors. If you see font-related issues, add system font packages in the Dockerfile (or install them in your build step).

Post-deploy smoke test:

- You can run a quick smoke test against your deployed app using the included script `scripts/smoke_test.py`:

  python scripts/smoke_test.py --url https://your-deploy-url

- There is also a GitHub Action workflow `Deploy smoke test` (manual run) that uses the secret `DEPLOY_URL`. To use it:
  - Add repository secret `DEPLOY_URL` set to your public service URL (e.g., https://ransom-example.onrender.com)
  - In GitHub -> Actions -> Deploy smoke test -> Run workflow

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

