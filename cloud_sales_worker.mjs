import fs from 'fs';

const RAW_CFG = process.env.COMPOSIO_MCP_CONFIG;
if (!RAW_CFG) {
  console.error('Missing COMPOSIO_MCP_CONFIG secret');
  process.exit(1);
}

const cfg = JSON.parse(RAW_CFG).mcpServers.composio;
const MCP_URL = cfg.url || cfg.serverUrl;
const HEADERS = {
  ...cfg.headers,
  'Content-Type': 'application/json',
  'Accept': 'application/json, text/event-stream'
};

const STATE_FILE = './cloud_state.json';
let state = { contactedEmails: [], repliedMessageIds: [], lastRun: null };
if (fs.existsSync(STATE_FILE)) {
  try {
    state = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
  } catch {}
}

const INITIAL_CONTACTED = [
  'info@drserkanaygin.com', 'info@badecanlar.com', 'soru@badecanlar.com',
  'hello@thepurestsolutions.com', 'info@estepera.com', 'info@dokuclinic.com',
  'bilgi@sinoz.com.tr', 'info@smilehairclinic.com', 'info@hermest.com.tr',
  'info@esteworld.com.tr', 'info@dentakay.com', 'info@drcinik.com',
  'info@estethica.com.tr', 'info@essiguzellik.com'
];
for (const e of INITIAL_CONTACTED) {
  if (!state.contactedEmails.includes(e.toLowerCase())) {
    state.contactedEmails.push(e.toLowerCase());
  }
}

async function callComposio(tools) {
  const res = await fetch(MCP_URL, {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'tools/call',
      params: {
        name: 'COMPOSIO_MULTI_EXECUTE_TOOL',
        arguments: {
          session_id: 'cloud247',
          sync_response_to_workbench: false,
          tools
        }
      }
    })
  });
  const text = await res.text();
  const dataLines = text.split('\n').filter(l => l.startsWith('data: '));
  if (dataLines.length === 0) throw new Error('Invalid MCP SSE response: ' + text.slice(0, 200));
  const rpc = JSON.parse(dataLines[dataLines.length - 1].slice(6));
  const innerText = rpc?.result?.content?.[0]?.text;
  return innerText ? JSON.parse(innerText) : rpc;
}

const TARGET_SITES = [
  { name: 'Vera Clinic', url: 'https://www.veraclinic.net/tr/iletisim/' },
  { name: 'Clinicana', url: 'https://www.clinicana.com/tr/iletisim/' },
  { name: 'Cosmed Dermokozmetik', url: 'https://www.cosmed.com.tr/iletisim' },
  { name: 'Maruderm Kozmetik', url: 'https://www.maruderm.com/iletisim' },
  { name: 'Asmed Hair Clinic', url: 'https://www.hairtransplantfue.org/tr/iletisim' },
  { name: 'Anadolu Sağlık / Estetik', url: 'https://www.anadolusaglik.org/iletisim' },
  { name: 'Acıbadem Beauty Center', url: 'https://www.acibadembeautycenter.com/iletisim/' },
  { name: 'Maya Estetik', url: 'https://www.mayaestetik.com/iletisim/' },
  { name: 'Hospitadent Diş Grubu', url: 'https://www.hospitadent.com/iletisim/' },
  { name: 'DentGroup', url: 'https://www.dentgroup.com.tr/iletisim' },
  { name: 'Ovadent Diş Kliniği', url: 'https://www.ovadent.com/iletisim/' },
  { name: 'Medicana Health', url: 'https://www.medicana.com.tr/iletisim' }
];

async function verifyMailto(siteUrl) {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 5000);
    const res = await fetch(siteUrl, {
      signal: controller.signal,
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
    });
    clearTimeout(timer);
    const html = await res.text();
    const m = html.match(/mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i);
    return m ? m[1].toLowerCase().trim() : null;
  } catch {
    return null;
  }
}

async function main() {
  console.log('🚀 Starting 24/7 Cloud Autonomous Sales Worker...');

  const inboxRes = await callComposio([
    {
      tool_slug: 'GMAIL_FETCH_EMAILS',
      arguments: {
        q: 'in:inbox -from:me -from:mailer-daemon -from:notifications@github.com -from:notifications@vercel.com -from:jobalerts-noreply@linkedin.com -from:hello@lemonsqueezy.com newer_than:2d',
        max_results: 8,
        include_payload: false,
        user_id: 'me'
      }
    }
  ]);

  const messages = inboxRes?.data?.results?.[0]?.response?.data?.messages || [];
  console.log(`📥 Checked Gmail Inbox: ${messages.length} recent non-system messages.`);

  for (const msg of messages) {
    const msgId = msg.messageId;
    const senderRaw = msg.sender || '';
    const emailMatch = senderRaw.match(/<([^>]+)>/) || [null, senderRaw];
    const senderEmail = (emailMatch[1] || '').toLowerCase().trim();
    if (!senderEmail || !senderEmail.includes('@')) continue;
    if (
      senderEmail.includes('noreply') ||
      senderEmail.includes('no-reply') ||
      senderEmail.includes('google.com') ||
      senderEmail.includes('github.com') ||
      senderEmail.includes('vercel.com') ||
      senderEmail.includes('linkedin.com')
    ) continue;

    if (state.repliedMessageIds.includes(msgId)) continue;
    if (['info@drserkanaygin.com', 'info@badecanlar.com', 'soru@badecanlar.com', 'hello@thepurestsolutions.com'].includes(senderEmail)) {
      state.repliedMessageIds.push(msgId);
      continue;
    }

    const brandGuess = senderEmail.split('@')[1].split('.')[0].toUpperCase();
    const encBrand = encodeURIComponent(brandGuess);
    const subj = msg.subject?.startsWith('Re:') ? msg.subject : `Re: ${msg.subject || 'Mobil randevu ve iletisim akisi'}`;

    console.log(`💳 Sending automatic Touch #2 closing link + VakıfBank IBAN to warm lead: ${senderEmail}`);
    await callComposio([
      {
        tool_slug: 'GMAIL_SEND_EMAIL',
        arguments: {
          recipient_email: senderEmail,
          subject: subj,
          thread_id: msg.threadId,
          is_html: false,
          body: `Merhaba ${brandGuess} Ekibi,\n\nNazik geri dönüşünüz için çok teşekkür ederim. İlgili ekibinizin doğrudan telefon veya bilgisayardan canlı test edebilmesi için hazırladığım özel interaktif karşılama ve hızlı WhatsApp dönüşüm ekranınız aşağıdadır:\n\n1) Canlı Mobil Karşılama & WhatsApp Randevu Vitrini (Tek Seferlik 350 TL - Aidatsız):\nhttps://hanubaki.github.io/orthostride-funnel/esnaf.html?biz=${encBrand}\n\n2) 3D AI Video & Reels Reklam Portföyü (500 TL):\nhttps://hanubaki.github.io/orthostride-funnel/ai-reklam-portfoy.html?marka=${encBrand}\n\nSistemi kendi kurumsal WhatsApp hattınıza ve işlem listenize göre 15 dakikada özelleştirip tüm kaynak dosyalarıyla teslim ediyorum.\n\nKurulumu başlatmak için resmi ödeme sayfamız:\nhttps://hanubaki.github.io/orthostride-funnel/odeme.html?v=3\n(VakıfBank FAST / Havale — Alıcı: Yusuf Akdemir | IBAN: TR06 0001 5001 5800 7313 5676 16)\n\nİyi çalışmalar dilerim,\nBerke Akdemir`
        }
      }
    ]);
    state.repliedMessageIds.push(msgId);
  }

  let sentCount = 0;
  for (const target of TARGET_SITES) {
    if (sentCount >= 2) break;
    const mailto = await verifyMailto(target.url);
    if (!mailto) continue;
    if (state.contactedEmails.includes(mailto)) continue;

    console.log(`📬 Sending verified Touch #1 (Zero-Spam) to ${target.name} (${mailto})...`);
    await callComposio([
      {
        tool_slug: 'GMAIL_SEND_EMAIL',
        arguments: {
          recipient_email: mailto,
          subject: `${target.name} mobil hasta karsilama ve iletisim akisi hakkinda not`,
          is_html: false,
          body: `Merhaba ${target.name} ekibi,\n\nWeb sitenizdeki online hasta ön değerlendirme ve WhatsApp iletişim akışını inceledim; mobil ziyaretçilerin daha hızlı randevu oluşturmasını sağlayacak kısa bir interaktif karşılama örneği hazırladım.\n\nİlgili dijital pazarlama veya kurumsal iletişim yetkilinize iletmem için bu e-posta adresi uygun mudur?\n\nİyi çalışmalar dilerim,\nBerke Akdemir`
        }
      }
    ]);
    state.contactedEmails.push(mailto);
    sentCount++;
  }

  state.lastRun = new Date().toISOString();
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), 'utf8');
  console.log(`✅ Cloud Worker finished cleanly. Sent ${sentCount} new verified Touch #1 emails.`);
}

main().catch(err => {
  console.error('Worker error:', err);
  process.exit(0);
});
