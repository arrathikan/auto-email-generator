import socket
import ipaddress
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# Unsafe IP networks that must never be accessed (SSRF protection)
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # Current network
    ipaddress.ip_network("10.0.0.0/8"),          # Private IPv4 Class A
    ipaddress.ip_network("100.64.0.0/10"),       # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),         # IPv4 Loopback
    ipaddress.ip_network("169.254.0.0/16"),      # IPv4 Link-local / Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),       # Private IPv4 Class B
    ipaddress.ip_network("192.0.0.0/24"),        # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),        # TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),      # Private IPv4 Class C
    ipaddress.ip_network("198.18.0.0/15"),       # Network benchmark tests
    ipaddress.ip_network("198.51.100.0/24"),     # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),      # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),         # Multicast
    ipaddress.ip_network("240.0.0.0/4"),         # Reserved / Future use
    ipaddress.ip_network("::/128"),              # IPv6 Unspecified
    ipaddress.ip_network("::1/128"),             # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),            # IPv6 Unique Local Address
    ipaddress.ip_network("fe80::/10"),           # IPv6 Link-local
    ipaddress.ip_network("ff00::/8"),            # IPv6 Multicast
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "169.254.169.254"
}

def is_safe_url(url: str) -> tuple[bool, str]:
    """
    Validates a URL against Server-Side Request Forgery (SSRF) threats.
    Enforces:
    - HTTP/HTTPS schemes only.
    - Disallows localhost, internal network names, and cloud metadata hostnames.
    - Resolves DNS to check all resulting IP addresses against blocked private/reserved CIDRs.
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty."

    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False, "Malformed URL format."

    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are permitted."

    hostname = (parsed.hostname or "").strip().lower()
    if not hostname:
        return False, "URL must include a valid hostname."

    # Check hostname blocklist
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(".local") or hostname.endswith(".internal"):
        return False, f"Access to internal or restricted host '{hostname}' is blocked for security."

    # DNS Resolution and IP validation
    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    try:
        addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return False, f"Could not resolve host '{hostname}'. Please check the URL domain."
    except Exception as e:
        return False, f"DNS resolution failed: {str(e)}"

    if not addr_info:
        return False, f"No IP addresses resolved for '{hostname}'."

    for family, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, f"Invalid resolved IP '{ip_str}'."

        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved or ip_obj.is_multicast or ip_obj.is_unspecified:
            return False, f"Destination resolved to a restricted or private network address ({ip_str})."

        for net in BLOCKED_IP_NETWORKS:
            if ip_obj in net:
                return False, f"Destination IP {ip_str} falls within a restricted network range."

    return True, "URL is safe."

def extract_job_posting_text(url: str, max_redirects: int = 3, timeout_seconds: int = 10) -> tuple[str, str | None]:
    """
    Safely retrieves and parses a public job posting URL with:
    - Strict SSRF defense (including redirect SSRF checks)
    - Timeout and max response size controls
    - Clean text extraction with BeautifulSoup
    - Detection of empty or unusable scraped content with clear fallback guidance
    """
    current_url = url.strip()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    # Redirect loop with SSRF verification at every hop
    for hop in range(max_redirects + 1):
        safe, reason = is_safe_url(current_url)
        if not safe:
            return "", f"Security validation failed: {reason}"

        try:
            response = requests.get(
                current_url,
                headers=headers,
                timeout=timeout_seconds,
                allow_redirects=False,
                stream=True
            )
        except requests.exceptions.Timeout:
            return "", "Connection timed out while fetching the job page (10s limit). Please copy and paste the job description directly."
        except requests.exceptions.RequestException as e:
            return "", f"Could not reach the job posting: {str(e)}. Please paste the job description directly."

        # Handle redirects manually to inspect destination IP
        if response.status_code in (301, 302, 303, 307, 308):
            redirect_target = response.headers.get("Location")
            if not redirect_target:
                return "", "Server responded with redirect but missing Location header."
            current_url = urljoin(current_url, redirect_target)
            continue

        if response.status_code != 200:
            return "", f"Job page returned HTTP status {response.status_code}. The page may require a login or captcha. Please copy and paste the job description directly."

        # Content length safeguard (max 5 MB)
        content_bytes = response.raw.read(5 * 1024 * 1024, decode_content=True)
        break
    else:
        return "", "Too many redirects encountered while loading the job posting."

    # Parse HTML using BeautifulSoup
    try:
        soup = BeautifulSoup(content_bytes, "html.parser")
        # Remove noisy, non-content HTML elements
        for element in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "aside", "form"]):
            element.decompose()

        text = soup.get_text(separator=" ", strip=True)
    except Exception as e:
        return "", f"HTML parsing error: {str(e)}. Please paste the job description directly."

    # Verify meaningful content
    words = text.split()
    if len(words) < 25 or len(text) < 120:
        return "", "Extracted page content was too short or empty (the page may be dynamically loaded by JavaScript or blocked). Please copy and paste the job description directly into the text box."

    return text, None
