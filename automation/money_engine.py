import re
import ssl
import urllib.request

PAYMENT_CONFIG = {
    "bank_name": "VakıfBank",
    "swift_bic": "TVBATR2A",
    "recipient_name": "Yusuf Akdemir",
    "iban_formatted": "TR06 0001 5001 5800 7313 5676 16",
    "iban_raw": "TR060001500158007313567616",
    "checkout_url": "https://hanubaki.github.io/orthostride-funnel/odeme.html",
    "cloud_fulfillment_zip": "https://hanubaki.github.io/orthostride-funnel/TESLIMAT_PAKETI_HAZIR.zip",
}

def extract_verified_mailto_email(domain: str):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    domain_clean = domain.lower().replace("www.", "").strip("/")
    domain_prefix = domain_clean.split(".")[0]
    mailto_matches = []
    for path in ["/contact-us/", "/contact/", "/iletisim/", ""]:
        url = f"https://www.{domain_clean}{path}"
        try:
            req = urllib.request.Request(url, headers=headers)
            html = urllib.request.urlopen(req, timeout=8, context=ctx).read().decode("utf-8", errors="ignore")
            found = re.findall(rf"mailto:([a-zA-Z0-9._%+-]+@{re.escape(domain_clean)})", html, re.I)
            for email in found:
                clean_email = email.lower().strip()
                if clean_email not in mailto_matches and not clean_email.startswith(f"{domain_prefix}@"):
                    mailto_matches.append(clean_email)
        except Exception:
            continue
    for pref in ("info@", "contact@", "iletisim@", "hello@", "support@", "destek@"):
        for email in mailto_matches:
            if email.startswith(pref):
                return email
    return mailto_matches[0] if mailto_matches else None
