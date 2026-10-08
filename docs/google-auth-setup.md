# Google Sign-In Setup

LearnMate uses Google Identity Services only to obtain an ID token. The
FastAPI backend verifies that signed token and then creates the same short-lived
LearnMate session used by email/password login. A Google client secret is not
needed for this flow and must not be added to the frontend.

## 1. Create the Google Web client

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select the project used for LearnMate.
3. Open **Google Auth Platform** and complete the app information and audience
   settings. If the app is in testing mode, add the Google accounts that will
   test it.
4. Open **Clients**, create an OAuth client, and choose **Web application**.
5. Add these **Authorized JavaScript origins** for local development:
   - `http://localhost:5173`
   - `http://127.0.0.1:5173`
6. No redirect URI is required for LearnMate's popup callback flow.
7. Copy the generated client ID ending in `.apps.googleusercontent.com`.

Google's official setup and button documentation:

- [Get a Google API client ID](https://developers.google.com/identity/gsi/web/guides/get-google-api-clientid)
- [Display the Sign in with Google button](https://developers.google.com/identity/gsi/web/guides/display-button)
- [Verify Google ID tokens on a backend](https://developers.google.com/identity/sign-in/web/backend-auth)

## 2. Configure LearnMate

In `backend/.env`, add:

```text
LEARNMATE_GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
```

In `frontend/.env`, add the same public Web client ID:

```text
VITE_GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
```

Both `.env` files are ignored by Git. Do not commit private keys, client
secrets, passwords, or LearnMate's JWT signing secret.

Install the backend requirements after pulling this feature:

```powershell
cd .\backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Restart and test

Environment values are read when each development server starts. Stop and
restart both servers after editing the `.env` files.

Use the **Sign in with Google** button on the account page. A successful Google
login should open the normal LearnMate Home screen. An invalid or unverified
Google token is rejected by the backend and does not create a LearnMate session.

Existing Gmail and Google Workspace password accounts can be linked when Google
is authoritative for the verified email. LearnMate does not silently merge an
existing password account that uses a third-party email domain; the student is
asked to use the password login instead.
