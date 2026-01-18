# Social-Hunt (Web + CLI)

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Windows Install (PowerShell)

```powershell
cd C:\path\to\social-hunt-webapp
py -m venv .venv
\.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## CLI

```bash
python -m social_hunt.cli afterpacket --format json
python -m social_hunt.cli afterpacket --platforms github reddit instagram
```

## Web (FastAPI)

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### Admin token (required for Settings + plugins)

Privileged endpoints (Settings, provider reload, plugin upload) are protected by an **admin token**.

Recommended (production):

```bash
export SOCIAL_HUNT_PLUGIN_TOKEN="...long random..."
```

Optional (web bootstrap): if you want to set the server token from the Token page,
enable bootstrap **temporarily**:

```bash
export SOCIAL_HUNT_ENABLE_TOKEN_BOOTSTRAP=1
```

Then visit `/` → Token → "Set / Rotate token".
After setting it, unset the env var and restart.

### Enable plugin uploads

Web uploads are disabled unless explicitly enabled:

```bash
export SOCIAL_HUNT_ENABLE_WEB_PLUGIN_UPLOAD=1
```

### Windows run

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Open:
- http://127.0.0.1:8000/

## Your IP (as seen by the API)

The web UI shows your IP using `/api/whoami`. This is helpful when running behind Apache/Nginx
to confirm `X-Forwarded-For` is being passed correctly.

## Notes
- Some platforms may return bot-walls (CAPTCHA / login). Those show as `blocked` or `unknown`.
- This is an OSINT presence checker for **public** profile pages.

## Metadata
Each result includes a best-effort `profile` object. For many sites this is pulled
from Open Graph / Twitter Card metadata (`og:title`, `og:image`, etc.).

Some providers use JSON endpoints/APIs when available:
- GitHub: public user endpoint can return avatar URL, followers/following, and `created_at`.
- Reddit: `/user/{username}/about.json` commonly exposes `created_utc` and karma fields.

## HIBP (Have I Been Pwned)

The built-in `hibp` provider can check for breach exposure (and optionally pastes) via the HIBP API.

Configure in Dashboard → Settings:

- `hibp_api_key` (required)
- `hibp_user_agent` (required by HIBP; set to something identifying your app)

By default, HIBP lookups run only when the input looks like an email address. You can override this
behavior with:

- `hibp_allow_non_email` = `1`

Creation dates are not public on many platforms; treat them as optional.
