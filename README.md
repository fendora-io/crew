# crew

> A daily DevSecOps signal digest, drafted in your voice, delivered to Telegram.

I built `crew` because I wanted to post consistently about DevSecOps, cloud security,
Kubernetes, and AI-native security on LinkedIn and X — but I didn't want to waste an
hour every morning trawling Hacker News, NVD, and GitHub Trending to find what to
write about, and another hour drafting.

`crew` does both:

1. **Every morning at 07:00**, it scans Hacker News, GitHub Trending, and the NVD
   CVE feed for fresh DevSecOps-relevant signals.
2. **It drafts a LinkedIn post and an X thread** for each, in your voice, using
   Claude. Your voice lives in a single prompt at the top of `crew.py` that you
   own and edit.
3. **It Telegrams you the digest** as copy-paste-ready code blocks.
4. **You pick one, copy, paste into LinkedIn/X, post.** Native posting, not
   scheduler. Done in 5 minutes.

That's it. No web UI. No SaaS. No scheduler. No publisher. ~650 lines of Python.

## Why this exists

If you're a founder, engineer, or security person trying to build a public voice
without burning two hours a day on it, you might find this useful too.

## What it costs to run

| Item | Monthly |
|---|---|
| VPS (Hetzner CX11 in Nuremberg) | €4.51 |
| Anthropic API (daily use, Sonnet) | ~€1-3 |
| **Total** | **~€10-15** |

No Typefully, no domain, no TLS, no third-party publisher.

## Quickstart

You need: a server (or any always-on machine), an Anthropic API key, and a
Telegram bot. Optionally an [Infisical](https://infisical.com) project if
you'd rather not keep plaintext secrets on disk.

```bash
git clone git@github.com:fendora-io/crew.git
cd crew
cp .env.example .env
# fill in EITHER the INFISICAL_* block (recommended)
# OR the secret values directly. See SETUP.md.

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test run
. .env && python crew.py
```

You should get a string of Telegram messages within ~30 seconds.

Once it works, drop it on cron:

```cron
0 6 * * * cd /opt/crew && . .env && ./venv/bin/python crew.py >> /var/log/crew.log 2>&1
```

Full step-by-step deployment in [SETUP.md](./SETUP.md).

## The two files you should edit

**[`crew.toml`](./crew.toml)** — keywords and topics, no Python required.
Add a keyword, save, done. Changes take effect on the next run.

```toml
[keywords]
include = ["nis2", "cra compliance", "sbom", ...]   # what to look for
exclude = ["layoffs", "sustainability", ...]         # what to ignore
cve_products = ["kubernetes", "nginx", ...]          # CVE filter
hn_fallback_topics = ["security", "devops", ...]    # HN fallback searches
```

**[`VOICE_SYSTEM_PROMPT`](./crew.py)** near the top of `crew.py`. That's the
editorial product. After a week of posting, you'll know what to add to the
banned-words list and what to tighten in the length rules. After a month, paste
3-5 of your own best posts into it as few-shot examples — the output quality
jump is bigger than any model upgrade.

The Python code is a delivery mechanism. The prompt is the brand.

## Daily flow

```
☕  07:00  Phone dings
   Read 3 drafts while making coffee
   Tap-and-hold the code block → Copy
   Open LinkedIn or X app → Paste → Edit a line → Post
   Reply `done 2` to the bot
   Done before coffee is cold
```

## Tuning

**Topics and keywords** — edit [`crew.toml`](./crew.toml), no code change needed:
- `keywords.include` — HN headline match keywords. Add EU regulatory terms, breach keywords, tool names.
- `keywords.exclude` — drops stories before Claude sees them (saves tokens).
- `keywords.cve_products` — which products make a CVE worth posting about.
- `keywords.hn_fallback_topics` — search terms used when the front page is quiet.

**Signal quality** — in [`crew.py`](./crew.py):
- `gather_signals` ranking — currently CVEs win, then HN by engagement, then GitHub.
  Adjust as you learn what produces your best posts.
- `VOICE_SYSTEM_PROMPT` — the actual editorial product. Edit weekly.
- Prompt caching ([docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)) caches the static voice prefix across the 2nd and 3rd draft in a run (~5 min window). Check server logs for `prompt cache read=…`.

**Preflight analysis** — every Telegram card opens with a colour-coded block before the
post content: recency (fresh/stale), factual flags, audience fit, and post risk (🟢/🟡/🔴).
No extra API call — it's part of the existing JSON output.

## Security

This bot handles API keys for Anthropic and Telegram. It does not handle any
keys with destructive write access to your accounts (no LinkedIn posting, no X
posting, no third-party publisher integrations) — by design. Worst-case
compromise: an attacker reads your draft posts and your Telegram chat ID.

For production we recommend storing secrets in [Infisical](https://infisical.com)
(EU or US cloud, or self-hosted) and authenticating with a read-only
Universal Auth machine identity scoped to the `/crew` path. The only
plaintext on disk is then the bootstrap client ID/secret. See
[SETUP.md](./SETUP.md#4-configure).

See [SECURITY.md](./SECURITY.md) for the threat model, disclosure process, and
operational hardening notes.

## Contributing

`crew` is intentionally small. PRs welcome for:

- New signal sources (Reddit, GitHub Security Advisories, vendor blogs)
- Better dedup / scoring logic
- Bug fixes

Not welcome:

- Posting integrations (Typefully, Buffer, native LinkedIn/X APIs). Manual
  posting is a feature, not a missing piece.
- Web UI, dashboards, multi-tenant. Single-user CLI is the design.
- "AI agent" framework rewrites. The whole thing is one Python file. It should
  stay that way.

## License

[MIT](./LICENSE).

## Author

Built by [Mohi](https://mohism.io/) at [Fendora](https://fendora.io).

- Mohi: [mohism.io](https://mohism.io/) ·
  [LinkedIn](https://www.linkedin.com/in/mohammadjalili/) ·
  [X](https://x.com/disismohi)
- Fendora: [fendora.io](https://fendora.io) ·
  [LinkedIn](https://www.linkedin.com/company/fendora) ·
  [X](https://x.com/fendora_io)

If `crew` helps you ship, the best thank-you is a post — tag the repo so others
can find it.
