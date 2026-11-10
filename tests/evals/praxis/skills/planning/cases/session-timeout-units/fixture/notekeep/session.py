"""The session cookie sent after login."""

from http.cookies import SimpleCookie

from notekeep.settings import SESSION_TIMEOUT_MINUTES


def session_cookie(token):
    cookie = SimpleCookie()
    cookie["session"] = token
    cookie["session"]["httponly"] = True
    cookie["session"]["max-age"] = SESSION_TIMEOUT_MINUTES
    return cookie.output(header="").strip()
