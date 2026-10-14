import os
import re
import subprocess

PAYMENT_CONFIG = {
    "bank_name": "VakıfBank",
    "swift_bic": "TVBATR2A",
    "recipient_name": "Yusuf Akdemir",
    "iban_formatted": "TR06 0001 5001 5800 7313 5676 16",
    "iban_raw": "TR060001500158007313567616",
    "checkout_url": "https://hanubaki.github.io/orthostride-funnel/odeme.html",
    "cloud_fulfillment_zip": "https://hanubaki.github.io/orthostride-funnel/TESLIMAT_PAKETI_HAZIR.zip",
    "sender_email": "berkeakdemir5855@gmail.com",
}

VERIFIED_TARGETS_BATCH = [
    {"name": "Dr. Serkan Aygin Clinic", "domain": "drserkanaygin.com", "email": "info@drserkanaygin.com"},
    {"name": "Turkey Hair Clinic", "domain": "turkeyhairclinic.com", "email": "info@turkeyhairclinic.com"},
    {"name": "Istanbul Care Clinic", "domain": "istanbul-care.com", "email": "info@istanbul-care.com"},
    {"name": "Istanbul Hair Institute", "domain": "istanbulhairinstitute.com", "email": "info@istanbulhairinstitute.com"},
    {"name": "Antalya Dental Clinic Turkey", "domain": "antalyadentalclinicturkey.com", "email": "info@antalyadentalclinicturkey.com"},
    {"name": "Medical Dental Turkey", "domain": "medicaldentalturkey.com", "email": "info@medicaldentalturkey.com"},
    {"name": "Estetik International", "domain": "estetikinternational.com", "email": "info@estetikinternational.com"},
    {"name": "Dentakay Dental Clinic", "domain": "dentakay.com", "email": "info@dentakay.com"},
    {"name": "Attelia Oral & Dental", "domain": "atteliadental.com", "email": "info@atteliadental.com"},
    {"name": "Hair of Istanbul", "domain": "hairofistanbul.com", "email": "info@hairofistanbul.com"},
    {"name": "Elithair", "domain": "elithairtransplant.com", "email": "contact@elithairtransplant.com"},
    {"name": "BlueMagic Group", "domain": "bluemagiclinic.com", "email": "enquiries@bluemagiclinic.com"},
    {"name": "Natural Clinic", "domain": "natural.clinic", "email": "info@natural.clinic"},
]


def _fetch_html(url: str) -> str:
    try:
        import ssl
        import urllib.request
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        return urllib.request.urlopen(req, timeout=8, context=ctx).read().decode("utf-8", errors="ignore")
    except Exception:
        res = subprocess.run(
            ["curl.exe", "-sL", "-k", "--max-time", "8", "-A", "Mozilla/5.0", url],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        return res.stdout or ""


def extract_verified_mailto_email(domain: str):
    domain_clean = domain.lower().replace("www.", "").strip("/")
    domain_prefix = domain_clean.split(".")[0]
    mailto_matches = []
    for path in ["/contact-us/", "/contact/", "/iletisim/", ""]:
        url = f"https://www.{domain_clean}{path}"
        try:
            html = _fetch_html(url)
            found = re.findall(rf"mailto:([a-zA-Z0-9._%+-]+@{re.escape(domain_clean)})", html, re.I)
            for email in found:
                clean_email = email.lower().strip()
                if clean_email not in mailto_matches and not clean_email.startswith(f"{domain_prefix}@"):
                    mailto_matches.append(clean_email)
            if mailto_matches:
                break
        except Exception:
            continue
    for pref in ("info@", "contact@", "iletisim@", "hello@", "support@", "destek@"):
        for email in mailto_matches:
            if email.startswith(pref):
                return email
    return mailto_matches[0] if mailto_matches else None


def build_email_payload(biz_name: str):
    from urllib.parse import quote
    enc = quote(biz_name)
    demo_tr = f"https://hanubaki.github.io/orthostride-funnel/esnaf.html?biz={enc}"
    demo_en = f"https://hanubaki.github.io/orthostride-funnel/advertorial.html?brand={enc}"
    pay_url = f"{PAYMENT_CONFIG['checkout_url']}?marka={enc}&fiyat=350%20TL"
    subject = f"{biz_name} — Hazır WhatsApp Randevu & Kampanya Funnel Demosu"
    body = (
        f"Merhaba {biz_name} Ekibi,\n\n"
        f"Instagram, Google ve uluslararası reklam trafiğinizden gelen danışanların 30 saniyede paket seçip "
        f"doğrudan WhatsApp hattınıza hazır randevu düşürmesi için {biz_name} adına özel canlı bir kampanya "
        f"ve ön-satış sistemi hazırladım:\n\n"
        f"1) Canlı Kampanya & WhatsApp Randevu Sayfanız:\n{demo_tr}\n\n"
        f"2) Uluslararası (İngilizce) Advertorial Ön-Satış Funnel'ınız:\n{demo_en}\n\n"
        f"3) Tek-Tık Ödeme & Anında Kaynak Kod Teslimatı (350 TL — Aylık Ücret Yok):\n{pay_url}\n\n"
        f"Linklerden canlı sisteminizi hemen test edebilirsiniz. Beğenirseniz tüm kaynak kod paketini "
        f"({PAYMENT_CONFIG['bank_name']} — Alıcı: {PAYMENT_CONFIG['recipient_name']} — {PAYMENT_CONFIG['iban_formatted']}) "
        f"üzerinden tek seferlik 350 TL'ye hemen teslim edebilirim.\n\n"
        f"İyi çalışmalar,\nBerke Akdemir"
    )
    return subject, body


def send_via_gmail_smtp(to_email: str, subject: str, body: str, app_password: str) -> tuple[bool, str]:
    sender = PAYMENT_CONFIG["sender_email"]
    ps_script = f"""
$ErrorActionPreference = 'Stop'
$smtp = New-Object System.Net.Mail.SmtpClient('smtp.gmail.com', 587)
$smtp.EnableSsl = $true
$smtp.Credentials = New-Object System.Net.NetworkCredential('{sender}', '{app_password.replace(" ", "")}')
$msg = New-Object System.Net.Mail.MailMessage('{sender}', '{to_email}', $env:MAIL_SUBJ, $env:MAIL_BODY)
$msg.BodyEncoding = [System.Text.Encoding]::UTF8
$msg.SubjectEncoding = [System.Text.Encoding]::UTF8
$smtp.Send($msg)
"""
    env = os.environ.copy()
    env["MAIL_SUBJ"] = subject
    env["MAIL_BODY"] = body
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], env=env, capture_output=True, text=True)
    return (res.returncode == 0, (res.stderr or res.stdout or "").strip())


def run_batch(app_password: str):
    sent = 0
    for item in VERIFIED_TARGETS_BATCH:
        subj, body = build_email_payload(item["name"])
        ok, info = send_via_gmail_smtp(item["email"], subj, body, app_password)
        status = "TESLIM EDILDI" if ok else f"HATA: {info}"
        print(f"[{status}] {item['name']} -> {item['email']}")
        if ok:
            sent += 1
    print(f"\nToplam Basarili Gonderim: {sent}/{len(VERIFIED_TARGETS_BATCH)}")


if __name__ == "__main__":
    import sys
    pwd = os.environ.get("GMAIL_APP_PASSWORD") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if pwd:
        run_batch(pwd)
    else:
        print("GMAIL_APP_PASSWORD eksik. Kullanim: python automation/money_engine.py <16_HANELI_GMAIL_UYGULAMA_SIFRESI>")


