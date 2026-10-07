# Authentication Security Notes

## Scope

LearnMate supports a local email/password method and Google Identity Services.
Both methods finish by issuing the same short-lived LearnMate JWT, so protected
document, quiz, recommendation and tutor endpoints keep one authorization
boundary.

These controls are suitable for the academic prototype. They are not a claim
that the local development system is production-ready.

## Implemented controls

- Local passwords are one-way hashed with Argon2 and are never returned by the
  API.
- Login errors do not reveal whether the email address or password was wrong.
- Google passwords are never handled by LearnMate. The browser supplies a
  signed Google ID token to the backend.
- The backend uses Google's authentication library to verify the signature,
  audience, issuer and expiry, and requires a verified email identity.
- Google's stable `sub` claim identifies the Google account. Email is not used
  as the federated primary identifier.
- Automatic linking to an existing password account is allowed only when
  Google is authoritative for the address: Gmail or a verified Google
  Workspace hosted domain. Other email collisions are rejected.
- LearnMate JWTs contain only the stable user ID and issued/expiry times. They
  are signed with an environment-provided secret and expire automatically.
- Authentication requests have two in-memory sliding-window limits:
  - five attempts per account identifier per 60 seconds;
  - twenty attempts per client address per 60 seconds.
- Account identifiers are SHA-256 hashed before they are used as in-memory
  limiter keys. A successful authentication clears that account's failure
  allowance.
- A rejected request returns HTTP `429` and a `Retry-After` header.
- Google client IDs are configuration rather than secrets. JWT secrets, API
  keys, tokens, passwords and local `.env` files remain excluded from Git.

The default limits can be adjusted with:

```text
LEARNMATE_AUTH_ACCOUNT_RATE_LIMIT_REQUESTS=5
LEARNMATE_AUTH_CLIENT_RATE_LIMIT_REQUESTS=20
LEARNMATE_AUTH_RATE_LIMIT_WINDOW_SECONDS=60
```

## Test evidence

Automated tests cover:

- password hashing and safe public user responses;
- valid, invalid and tampered LearnMate JWTs;
- Google account creation and repeat login by stable subject;
- safe linking of an existing Gmail account;
- rejection of unsafe third-party email linking;
- rejection of invalid and unverified Google credentials;
- exact rate-limit boundaries and `Retry-After`;
- allowance recovery after the configured time window;
- clearing account failures after a successful login;
- limiting invalid Google tokens before repeated external verification; and
- migration of existing SQLite users without losing their records.

## Residual prototype risks

- The JWT is kept in browser `sessionStorage`. This limits persistence to the
  tab, but a successful cross-site scripting attack could still read it.
- Local development uses HTTP. Credentials and tokens require HTTPS in any
  deployed environment.
- The in-memory limiter is per backend process. A production deployment with
  multiple workers needs a shared store such as Redis and trusted-proxy-aware
  client identification.
- Local password accounts do not yet include email verification, password
  recovery or multi-factor authentication.
- There is no production session revocation, security-event monitoring or
  Google Cross Account Protection integration.

## Production recommendations

1. Replace browser token storage with a backend-managed session in an
   `HttpOnly`, `Secure`, `SameSite` cookie.
2. Enforce HTTPS and production security headers, including a Content Security
   Policy compatible with Google Identity Services.
3. Move rate-limit state to a shared service and monitor rejected attempts
   without logging passwords, Google credentials or raw email addresses.
4. Add verified-email recovery, optional MFA, session revocation and security
   event alerts.
5. Repeat penetration and authorization tests in the deployed environment.

References:

- [Google: authenticate with a backend server](https://developers.google.com/identity/sign-in/web/backend-auth)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
