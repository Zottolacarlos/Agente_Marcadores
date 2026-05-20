import httpx


def validate_url(url: str, timeout: float = 8) -> str:
    try:
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            resp = client.get(url)
        if 200 <= resp.status_code < 300:
            return "OK"
        if 300 <= resp.status_code < 400:
            return "REDIRECTED"
        if resp.status_code == 403:
            return "FORBIDDEN"
        if resp.status_code in (404, 410):
            return "BROKEN"
        return "UNKNOWN"
    except httpx.TimeoutException:
        return "TIMEOUT"
    except Exception:
        return "UNKNOWN"
