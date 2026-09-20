"""
NiPlex Harness — Built-in DuckDuckGo web search (no API key required) + single-page reading.
"""
from __future__ import annotations
import ipaddress
import re
import socket
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from security.content_guard import guard_external_content

DDG = "https://html.duckduckgo.com/html/"
_UA = "NiPlexHarness/1.0 (personal agent)"


def _is_private_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        return True
    if ip.version == 4:
        if ip in ipaddress.IPv4Network("10.0.0.0/8"):
            return True
        if ip in ipaddress.IPv4Network("172.16.0.0/12"):
            return True
        if ip in ipaddress.IPv4Network("192.168.0.0/16"):
            return True
        if str(ip) == "169.254.169.254":
            return True
    return False


def _resolve_hostname(hostname: str) -> Optional[str]:
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
        if addr_info:
            return addr_info[0][4][0]
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET6, socket.SOCK_STREAM)
        if addr_info:
            return addr_info[0][4][0]
    except (socket.gaierror, socket.timeout, OSError):
        pass
    return None


def _is_blocked_host(hostname: str) -> bool:
    if not hostname:
        return True
    host = hostname.lower().strip()

    if host in {"localhost", "0.0.0.0", "::1", "127.0.0.1"}:
        return True
    if host.endswith(".local") or host.endswith(".localhost"):
        return True

    try:
        ip = ipaddress.ip_address(host)
        if _is_private_ip(ip):
            return True
    except ValueError:
        pass

    resolved_ip = _resolve_hostname(host)
    if resolved_ip:
        try:
            ip = ipaddress.ip_address(resolved_ip)
            if _is_private_ip(ip):
                return True
        except ValueError:
            pass

    return False


def web_search(query: str, max_results: int = 5) -> str:
    query = (query or "").strip()
    if not query:
        return "Empty query."
    max_results = max(1, min(int(max_results or 5), 8))
    try:
        with httpx.Client(timeout=20, follow_redirects=True, headers={"User-Agent": _UA}) as client:
            r = client.post(DDG, data={"q": query})
            r.raise_for_status()
            html = r.text
        results = _parse(html, max_results)
        if not results:
            return f"No DuckDuckGo results for: {query}"
        lines = [f"DuckDuckGo results for: {query}"]
        for i, item in enumerate(results, 1):
            lines.append(f"{i}. {item['title']}\n   {item['url']}\n   {item['snippet']}")
        text = "\n".join(lines)
        return guard_external_content(text, "web_search results")
    except Exception as e:
        return f"Web search error: {type(e).__name__}"


def web_read(url: str, max_chars: int = 8000) -> str:
    url = (url or "").strip()
    if not url:
        return "Empty URL."
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "Only http/https URLs are supported."
    if _is_blocked_host(parsed.hostname or ""):
        return "Refusing to fetch a private/internal address."
    try:
        with httpx.Client(timeout=20, follow_redirects=False, headers={"User-Agent": _UA}) as client:
            current_url = url
            max_redirects = 5
            redirect_count = 0
            final_response = None

            while redirect_count < max_redirects:
                r = client.get(current_url)
                final_response = r

                if r.status_code in (301, 302, 303, 307, 308):
                    location = r.headers.get("location")
                    if not location:
                        return "Redirect without Location header."

                    if location.startswith("/"):
                        from urllib.parse import urljoin
                        location = urljoin(current_url, location)

                    parsed_redirect = urlparse(location)
                    if _is_blocked_host(parsed_redirect.hostname or ""):
                        return "Refusing to follow redirect to a private/internal address."

                    current_url = location
                    redirect_count += 1
                    continue

                r.raise_for_status()
                break

            if redirect_count >= max_redirects:
                return "Too many redirects."

            if final_response is None:
                return "No response received."

        content_type = final_response.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            return f"Unsupported content-type for reading: {content_type or 'unknown'}"
        text = _html_to_text(final_response.text)[:max_chars]
        if not text.strip():
            return f"No readable text found at {url}"
        return guard_external_content(f"Content from {url}:\n\n{text}", f"web page {url}")
    except Exception as e:
        return f"web_read error: {type(e).__name__}"


def _html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<br\s*/?>", "\n", html)
    html = re.sub(r"(?is)</p>", "\n\n", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    import html as _htmlmod
    text = _htmlmod.unescape(text)
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def _parse(html: str, limit: int) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    blocks = re.findall(
        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?class="result__snippet"[^>]*>(.*?)</',
        html,
        flags=re.S | re.I,
    )
    if not blocks:
        hrefs = re.findall(r'uddg=([^&"]+)', html)
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, flags=re.S)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</', html, flags=re.S)
        from urllib.parse import unquote
        for i in range(min(limit, len(hrefs), len(titles))):
            results.append({
                "url": unquote(hrefs[i]),
                "title": _strip_tags(titles[i]),
                "snippet": _strip_tags(snippets[i]) if i < len(snippets) else "",
            })
        return results[:limit]

    from urllib.parse import unquote, parse_qs, urlparse as _urlparse
    for href, title, snippet in blocks[:limit]:
        url = href
        if "uddg=" in href:
            qs = parse_qs(_urlparse(href).query)
            url = unquote(qs.get("uddg", [href])[0])
        results.append({"url": url, "title": _strip_tags(title), "snippet": _strip_tags(snippet)})
    return results


def _strip_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return " ".join(text.split())[:300]
