"""Standalone HTML, no CDN, no remote scripts, no telemetry."""
import json
from pathlib import Path
from urllib.parse import urlsplit
from .locales import locale_script, language


def write_report(result, path, *, context=None, lang="en"):
    """Write an audit report, optionally annotated with provenance and protocol.

    Report context is presentation metadata, outside the audit fingerprint.
    Only HTTP(S) source links are accepted; all text is rendered as text nodes.
    """
    language(lang)
    payload_data = dict(result)
    if context is not None:
        if not isinstance(context, dict):
            raise ValueError("report context must be an object")
        allowed = {"title", "protocol", "source_name", "source_url", "license", "notes"}
        if set(context) - allowed or any(not isinstance(v, str) for v in context.values()):
            raise ValueError("report context accepts only documented string fields")
        url = context.get("source_url")
        if url:
            parts = urlsplit(url)
            if parts.scheme not in {"http", "https"} or not parts.netloc or parts.username or parts.password:
                raise ValueError("source_url must be an absolute HTTP(S) URL without credentials")
        payload_data["report_context"] = dict(context)
    template = Path(__file__).with_name("report.html").read_text(encoding="utf-8")
    # Never allow user text to terminate the JSON script element.
    payload = json.dumps(payload_data, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    page = template.replace("__AUDIT_DATA__", payload)
    page=page.replace('<html lang="en">',f'<html lang="{lang}">').replace("<script>\n'use strict';", '<script>'+locale_script(lang)+"</script><script>\n'use strict';")
    Path(path).write_text(page, encoding="utf-8")
