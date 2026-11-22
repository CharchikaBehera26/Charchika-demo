import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import current_app


class SupabaseAuthError(Exception):
    pass


def google_authorization_url(redirect_to, code_challenge):
    base_url, _api_key = _auth_config()
    query = urlencode({
        "provider": "google",
        "redirect_to": redirect_to,
        "code_challenge": code_challenge,
        "code_challenge_method": "s256",
    })
    return f"{base_url}/auth/v1/authorize?{query}"


def exchange_google_code(auth_code, code_verifier):
    return _auth_request(
        "token?grant_type=pkce",
        {"auth_code": auth_code, "code_verifier": code_verifier},
    )


def revoke_auth_session(access_token):
    _auth_request("logout?scope=local", {}, access_token=access_token)


def _auth_config():
    base_url = current_app.config.get("SUPABASE_URL", "").rstrip("/")
    api_key = current_app.config.get("SUPABASE_ANON_KEY", "")
    if not base_url or not api_key:
        raise SupabaseAuthError("Supabase Auth is not configured.")
    return base_url, api_key


def _auth_request(path, payload, access_token=None):
    base_url, api_key = _auth_config()
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    request = Request(
        f"{base_url}/auth/v1/{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            response_body = response.read()
    except HTTPError as exc:
        raise SupabaseAuthError(
            f"Supabase Auth returned HTTP {exc.code}."
        ) from exc
    except (TimeoutError, URLError) as exc:
        raise SupabaseAuthError("Could not reach Supabase Auth.") from exc

    if not response_body:
        return {}
    try:
        result = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise SupabaseAuthError(
            "Supabase Auth returned an invalid response."
        ) from exc
    if not isinstance(result, dict):
        raise SupabaseAuthError("Supabase Auth returned an invalid response.")
    return result
