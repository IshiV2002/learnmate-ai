# LearnMate Image OCR Setup

LearnMate uses PyMuPDF with local Tesseract English language data to extract
searchable text from PNG and JPEG uploads. Tesseract is a system dependency, so
each developer must configure it on their own computer.

The backend needs the directory containing `eng.traineddata`. Adding the
`tesseract` command to the shell `PATH` is helpful but is not required by
LearnMate because the application passes the language-data directory directly
to PyMuPDF.

## Fix the common placeholder problem

Open `backend/.env`. If it contains this unchanged placeholder, remove or
comment out the line:

```text
LEARNMATE_TESSDATA_PATH=replace_with_your_local_tessdata_directory
```

That placeholder is not a real directory and prevents automatic discovery.

## Windows setup

### 1. Check the common installation location

Run in PowerShell:

```powershell
Test-Path "C:\Program Files\Tesseract-OCR\tessdata\eng.traineddata"
```

If the result is `True`, add this to `backend/.env`:

```text
LEARNMATE_TESSDATA_PATH=C:\Program Files\Tesseract-OCR\tessdata
```

If Tesseract was installed for only the current user, also check:

```powershell
Test-Path "$env:LOCALAPPDATA\Programs\Tesseract-OCR\tessdata\eng.traineddata"
```

When that result is `True`, use the corresponding expanded folder in
`backend/.env`, for example:

```text
LEARNMATE_TESSDATA_PATH=C:\Users\YOUR_WINDOWS_NAME\AppData\Local\Programs\Tesseract-OCR\tessdata
```

Do not commit `backend/.env`.

### 2. Install Tesseract if neither path exists

Follow the Windows section of the
[official Tesseract installation guide](https://tesseract-ocr.github.io/tessdoc/Installation.html).
Make sure English language data is selected so the installation contains:

```text
eng.traineddata
```

The official documentation links to the maintained third-party Windows
installer because modern Tesseract does not publish an official Windows
installer.

## Linux setup

Install Tesseract and English data using the package manager for the
distribution. On Debian or Ubuntu this is commonly:

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-eng
```

Common language-data locations include:

```text
/usr/share/tesseract-ocr/5/tessdata
/usr/share/tessdata
```

Set `LEARNMATE_TESSDATA_PATH` in `backend/.env` only when automatic discovery
does not find the correct location.

## macOS setup

Install Tesseract using Homebrew:

```bash
brew install tesseract
brew info tesseract
```

Use the `tessdata` directory reported under the Homebrew installation when an
explicit `LEARNMATE_TESSDATA_PATH` is needed.

## Verify LearnMate's configuration

Restart the backend after changing `.env`; configuration is loaded when the
Python application starts.

From the repository root on Windows:

```powershell
cd .\backend
.\.venv\Scripts\python.exe -c "from app.core.config import TESSDATA_DIRECTORY; print('Tessdata:', TESSDATA_DIRECTORY); print('English data found:', bool(TESSDATA_DIRECTORY and (TESSDATA_DIRECTORY / 'eng.traineddata').is_file()))"
```

Expected output ends with:

```text
English data found: True
```

Then restart the API:

```powershell
$env:LEARNMATE_JWT_SECRET_KEY = "your-local-secret-of-at-least-32-characters"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Use a private local JWT secret and never commit it.

## If the error continues

1. Confirm the configured directory contains `eng.traineddata`, not merely the
   `tesseract.exe` file.
2. Check for quotes or spelling mistakes in `backend/.env`.
3. Restart Uvicorn completely after changing the environment.
4. Run the verification command above from the `backend` directory.
5. Confirm the backend process is using the same repository and virtual
   environment that you configured.
