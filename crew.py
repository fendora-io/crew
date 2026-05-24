"""
crew — daily DevSecOps signal digest, drafted in your voice, delivered to Telegram.

Usage:
  python crew.py              # fetch signals, draft posts, send Telegram digest

Cron (06:00 UTC = 07:00 CET winter / 08:00 CEST summer):
  0 6 * * * cd /opt/crew && . .env && ./venv/bin/python crew.py

Secrets:
  Two supported paths, in priority order:
  1. Infisical (eu.infisical.com or self-hosted) via Universal Auth — set
     INFISICAL_CLIENT_ID + INFISICAL_CLIENT_SECRET + INFISICAL_PROJECT_ID
     and crew pulls ANTHROPIC_API_KEY / TELEGRAM_* / NVD_API_KEY at startup.
  2. Plain environment (.env file) — set the secrets directly.
  Plain env always wins over Infisical for any given key (so local overrides work).

Project: https://github.com/fendora-io/crew
License: MIT
"""

import os
import json
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

import requests
from anthropic import Anthropic


# ============================================================
# Secret loading — Infisical (optional) → process env
# ============================================================
def _load_infisical_secrets() -> None:
    """Pull secrets from Infisical into os.environ if INFISICAL_CLIENT_ID is set.

    Existing values in os.environ are NEVER overwritten — local .env always wins.
    No-op (silent) when INFISICAL_CLIENT_ID is unset, so deployments without
    Infisical keep working with a plain .env file.
    """
    client_id = os.environ.get("INFISICAL_CLIENT_ID")
    if not client_id:
        return

    client_secret = os.environ.get("INFISICAL_CLIENT_SECRET")
    project_id = os.environ.get("INFISICAL_PROJECT_ID")
    if not client_secret or not project_id:
        print(
            "WARN: INFISICAL_CLIENT_ID is set but INFISICAL_CLIENT_SECRET or "
            "INFISICAL_PROJECT_ID is missing — skipping Infisical fetch.",
            file=sys.stderr,
        )
        return

    host = os.environ.get("INFISICAL_HOST", "https://eu.infisical.com")
    env_slug = os.environ.get("INFISICAL_ENV", "prod")
    secret_path = os.environ.get("INFISICAL_SECRET_PATH", "/")

    try:
        from infisical_sdk import InfisicalSDKClient
    except ImportError:
        print(
            "WARN: INFISICAL_CLIENT_ID is set but `infisicalsdk` is not installed. "
            "Run: pip install infisicalsdk — falling back to plain env.",
            file=sys.stderr,
        )
        return

    try:
        client = InfisicalSDKClient(host=host)
        client.auth.universal_auth.login(
            client_id=client_id, client_secret=client_secret
        )
        resp = client.secrets.list_secrets(
            project_id=project_id,
            environment_slug=env_slug,
            secret_path=secret_path,
            expand_secret_references=True,
            view_secret_value=True,
            recursive=False,
            include_imports=True,
        )
    except Exception as e:
        print(f"ERROR: Infisical fetch failed: {e}", file=sys.stderr)
        raise

    secrets = getattr(resp, "secrets", None) or resp.get("secrets", [])
    pulled = 0
    for s in secrets:
        key = getattr(s, "secretKey", None) or s.get("secretKey")
        val = getattr(s, "secretValue", None) or s.get("secretValue")
        if not key or val is None:
            continue
        if key in os.environ:
            continue
        os.environ[key] = val
        pulled += 1
    print(
        f"crew: loaded {pulled} secrets from Infisical "
        f"({host}, env={env_slug}, path={secret_path})",
        file=sys.stderr,
    )


_load_infisical_secrets()


# ============================================================
# Config — from environment (populated by Infisical and/or .env)
# ============================================================
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
# Optional: post into a specific topic of a forum-enabled supergroup.
# Get the thread ID from the `message_thread_id` field in /getUpdates.
TELEGRAM_THREAD_ID = os.environ.get("TELEGRAM_THREAD_ID")
DB_PATH = os.environ.get("CREW_DB_PATH", "./state.db")
MODEL = os.environ.get("CREW_MODEL", "claude-opus-4-5")

ANTHROPIC = Anthropic(api_key=ANTHROPIC_KEY)

# ============================================================
# Your voice. This is the entire product.
# Edit weekly as you learn what works.
# ============================================================
VOICE_SYSTEM_PROMPT = """You are drafting LinkedIn and X posts for a 10-year engineer
who founded a DevSecOps / AppSec startup in Berlin. They're building thought leadership
around modern startup infrastructure, AI-native security, cloud engineering, Kubernetes,
CI/CD, platform engineering, and practical DevSecOps.

VOICE RULES — these are absolute:
- Sharp, opinionated, technically accurate, easy to understand.
- Specific numbers, binaries, CVE IDs, error messages — never abstractions.
- Use "I" not "we". Engineer voice, not consultant voice.
- Take a side. Be willing to be wrong publicly.
- End with one concrete action a reader can take Monday morning.

BANNED WORDS: leverage, synergy, holistic, robust, best-in-class, industry-leading,
thought leader, posture, journey, unlock, empower, seamless, mission-critical,
game-changer, revolutionize, paradigm shift.
Also banned: motivational closers, hashtag soup, em-dash-heavy aphorisms,
"Hot take:", "Unpopular opinion:", "Let that sink in."

LENGTHS:
- LinkedIn: 900-1400 chars. Hook in first 2 lines (before the "see more" cut).
  Short paragraphs (1-3 lines). Line breaks for breathing room.
- X thread: 5-8 tweets, each <=270 chars. First tweet is the hook + promise.
  Each subsequent tweet stands alone but earns the next.
- Hook: one line, under 100 chars, quotable.

OUTPUT FORMAT — return strict JSON only, no preamble, no code fences:
{
  "why_it_matters": "1-2 sentences on the engagement angle and who it's for",
  "linkedin": "the full LinkedIn post, with actual line breaks",
  "x_thread": ["tweet 1 text", "tweet 2 text", ...],
  "hook": "one quotable line"
}
"""

# ============================================================
# State — dedup signals across runs
# ============================================================
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS seen (
        signal_id TEXT PRIMARY KEY,
        first_seen TEXT NOT NULL
    )""")
    return conn


def already_seen(signal_id: str) -> bool:
    with db() as conn:
        return conn.execute(
            "SELECT 1 FROM seen WHERE signal_id = ?", (signal_id,)
        ).fetchone() is not None


def mark_seen(signal_id: str):
    with db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen VALUES (?, ?)",
            (signal_id, datetime.now(timezone.utc).isoformat()),
        )


# ============================================================
# Signal sources
# ============================================================
DEVSECOPS_KEYWORDS = (
    "security", "vulnerab", "cve", "kubernetes", "k8s", "docker",
    "container", "devops", "platform engineering", "supply chain",
    "ci/cd", "ci cd", "github actions", "mcp ", "ai agent",
    "prompt injection", "ebpf", "sigstore", "slsa", "argocd",
    "helm", "terraform", "opa", "kyverno", "cilium", "istio",
)

CVE_RELEVANT_PRODUCTS = (
    "kubernetes", "docker", "container", "containerd", "runc",
    "github action", "gitlab", "ci/cd", "supply chain",
    "npm", "pypi", "mcp", "linux kernel", "openssh", "nginx",
    "vault", "argocd", "helm", "terraform", "opa", "kyverno",
)


def fetch_hn() -> list[dict]:
    """Top HN stories matching DevSecOps keywords."""
    r = requests.get(
        "https://hn.algolia.com/api/v1/search",
        params={"tags": "front_page", "numericFilters": "points>80"},
        timeout=10,
    )
    r.raise_for_status()
    out = []
    for hit in r.json().get("hits", []):
        title = (hit.get("title") or "").lower()
        if any(k in title for k in DEVSECOPS_KEYWORDS):
            out.append({
                "id": f"hn:{hit['objectID']}",
                "source": "Hacker News",
                "title": hit.get("title"),
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}",
                "points": hit.get("points", 0),
                "comments": hit.get("num_comments", 0),
            })
    return out


def fetch_github_trending() -> list[dict]:
    """Today's trending repos (scrape — no auth required)."""
    r = requests.get(
        "https://github.com/trending?since=daily",
        timeout=10,
        headers={"User-Agent": "crew-bot/1.0 (+https://github.com/fendora-io/crew)"},
    )
    r.raise_for_status()
    out = []
    for m in re.finditer(r'<h2 class="h3 lh-condensed">\s*<a href="([^"]+)"', r.text):
        path = m.group(1).strip()
        out.append({
            "id": f"gh:{path}",
            "source": "GitHub Trending",
            "title": path.lstrip("/"),
            "url": f"https://github.com{path}",
        })
    return out[:15]


def fetch_cves() -> list[dict]:
    """Recent HIGH-severity CVEs from NVD, filtered to DevSecOps-relevant products."""
    since = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%dT00:00:00.000")
    until = datetime.now(timezone.utc).strftime("%Y-%m-%dT23:59:59.999")
    headers = {}
    if os.environ.get("NVD_API_KEY"):
        headers["apiKey"] = os.environ["NVD_API_KEY"]
    r = requests.get(
        "https://services.nvd.nist.gov/rest/json/cves/2.0",
        params={"pubStartDate": since, "pubEndDate": until, "cvssV3Severity": "HIGH"},
        headers=headers,
        timeout=15,
    )
    r.raise_for_status()
    out = []
    for v in r.json().get("vulnerabilities", [])[:30]:
        cve = v["cve"]
        cve_id = cve["id"]
        desc = next(
            (d["value"] for d in cve.get("descriptions", []) if d["lang"] == "en"),
            "",
        )
        if not any(k in desc.lower() for k in CVE_RELEVANT_PRODUCTS):
            continue
        out.append({
            "id": f"cve:{cve_id}",
            "source": "NVD",
            "title": f"{cve_id}: {desc[:250]}",
            "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
        })
    return out


def gather_signals() -> list[dict]:
    """Run all sources, dedup, rank, return top 3."""
    candidates = []
    for fn in (fetch_hn, fetch_github_trending, fetch_cves):
        try:
            candidates.extend(fn())
        except Exception as e:
            print(f"WARN: {fn.__name__} failed: {e}", file=sys.stderr)

    fresh = [c for c in candidates if not already_seen(c["id"])]

    def score(c):
        if c["source"] == "NVD":
            return 10_000  # CVEs always win
        if c["source"] == "Hacker News":
            return c.get("points", 0) + c.get("comments", 0) * 2
        return 50  # GitHub trending is fallback

    fresh.sort(key=score, reverse=True)
    return fresh[:3]


# ============================================================
# Drafting
# ============================================================
def draft_post(signal: dict) -> dict:
    user_msg = f"""Signal to write about:

Source: {signal['source']}
Title: {signal['title']}
URL: {signal['url']}

Draft posts following the voice rules. Return JSON only."""
    resp = ANTHROPIC.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=VOICE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = resp.content[0].text.strip()
    # Defensive: strip code fences if the model added them despite instructions
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip("` \n")
    return json.loads(text)


# ============================================================
# Telegram
# ============================================================
def tg_send(text: str):
    """Send a message. Telegram limit is 4096 chars; chunk if needed."""
    for chunk in _chunk(text, 4000):
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        if TELEGRAM_THREAD_ID:
            payload["message_thread_id"] = int(TELEGRAM_THREAD_ID)
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json=payload,
            timeout=10,
        )
        if r.status_code != 200:
            # Markdown can choke on stray underscores/asterisks — fall back to plain
            payload.pop("parse_mode", None)
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json=payload,
                timeout=10,
            )


def _chunk(text: str, size: int) -> list[str]:
    if len(text) <= size:
        return [text]
    chunks, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > size:
            chunks.append(cur)
            cur = line
        else:
            cur = f"{cur}\n{line}" if cur else line
    if cur:
        chunks.append(cur)
    return chunks


def send_digest(items: list[dict]):
    """One header, then per-signal cards with copy-paste-ready code blocks."""
    date = datetime.now(timezone.utc).strftime("%A, %d %B")
    tg_send(
        f"☕ *Morning. {date}.*\n"
        f"{len(items)} signals worth posting about today.\n"
        f"Each block below is in a code fence — tap and hold to copy."
    )

    for i, item in enumerate(items, 1):
        sig = item["signal"]
        d = item["draft"]

        header = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"*Option {i} — {sig['source']}*\n"
            f"_{sig['title'][:200]}_\n"
            f"[source]({sig['url']})\n\n"
            f"*Why it matters:* {d['why_it_matters']}\n\n"
            f"*Hook:*\n```\n{d['hook']}\n```"
        )
        tg_send(header)

        li = d["linkedin"]
        tg_send(f"*📘 LinkedIn* ({len(li)} chars)\n```\n{li}\n```")

        tg_send(f"*🐦 X thread* ({len(d['x_thread'])} tweets)")
        for j, tweet in enumerate(d["x_thread"], 1):
            tg_send(f"*{j}/{len(d['x_thread'])}* ({len(tweet)} chars)\n```\n{tweet}\n```")

    tg_send(
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Reply `done N` once you've posted option N.\n"
        "Reply `skip` to mark all as seen."
    )


def check_replies():
    """Poll Telegram for new messages, ack done/skip. Dedup is handled at draft time."""
    state_file = os.environ.get("CREW_TG_STATE", "./last_update.txt")
    last_id = 0
    if os.path.exists(state_file):
        with open(state_file) as f:
            last_id = int(f.read().strip() or 0)

    r = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
        params={"offset": last_id + 1, "timeout": 0},
        timeout=10,
    )
    updates = r.json().get("result", [])
    for u in updates:
        last_id = max(last_id, u["update_id"])
        msg = u.get("message", {}).get("text", "").strip().lower()
        if msg in ("skip", "/skip"):
            tg_send("👌 Skipped.")
        elif msg.startswith("done"):
            tg_send("✅ Got it.")

    with open(state_file, "w") as f:
        f.write(str(last_id))


# ============================================================
# Main
# ============================================================
def main():
    signals = gather_signals()
    if not signals:
        tg_send(
            "☕ No fresh signals today. Browse "
            "[HN](https://news.ycombinator.com) or "
            "[GitHub Trending](https://github.com/trending) manually."
        )
        return

    drafts = []
    for s in signals:
        try:
            drafts.append({"signal": s, "draft": draft_post(s)})
            mark_seen(s["id"])
        except Exception as e:
            print(f"WARN: drafting {s['id']} failed: {e}", file=sys.stderr)
            tg_send(f"⚠️ Drafting failed for: {s['title'][:100]}\nError: {e}")

    if not drafts:
        tg_send("⚠️ Found signals but all drafting attempts failed. Check logs.")
        return

    send_digest(drafts)

    try:
        check_replies()
    except Exception as e:
        print(f"WARN: reply check failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
