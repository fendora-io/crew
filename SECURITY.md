# Security Policy

`crew` is a small open-source tool published under [Fendora](https://fendora.io),
a DevSecOps company. We take security of this project seriously — both because
of who we are and because `crew` handles API credentials with real cost
implications.

## Supported versions

`crew` is currently single-versioned (latest `main`). Security fixes will be
applied to `main` and released as patch tags. There are no LTS branches.

| Version | Supported |
|---|---|
| `main` (latest) | ✅ |
| Older tags | ❌ |

## Reporting a vulnerability

Please **do not** open a public issue for security bugs.

Email: `security@fendora.io`

Include:
- A clear description of the issue
- Steps to reproduce (or a proof-of-concept)
- The version / commit SHA you tested against
- Your name and a contact handle (for credit, if you want it)

**Response targets:**
- Initial reply: within 3 business days
- Triage decision (accept / dispute / dupe): within 7 business days
- Fix or mitigation for accepted issues: within 30 days for high/critical,
  90 days for medium/low

**Disclosure:** we coordinate disclosure with reporters. Default: fix released
publicly first, write-up + credit follows within 14 days. If you need a faster
or slower timeline, say so in the report.

**Safe harbor:** we will not pursue legal action against good-faith security
research on `crew` that follows this policy: testing against your own deployment,
not against shared infrastructure; not exfiltrating user data; giving us
reasonable time to fix before public disclosure.

## Threat model

`crew` is a single-user CLI tool that runs as a cron job on a server you
control. The realistic threat model is narrow:

### In scope

| Threat | Mitigation |
|---|---|
| Leaked Anthropic API key → unbounded LLM spend | Hard monthly cap in Anthropic console; never log the key |
| Leaked Telegram bot token → attacker DMs you fake digests or reads your replies | Bot only talks to your `TELEGRAM_CHAT_ID`; rotate token if leaked |
| Prompt injection in fetched signals (HN title, CVE description, repo name) trying to manipulate drafts | Drafts are reviewed by you before posting; never auto-published |
| Compromised dependency in `requirements.txt` | Pinned versions; Dependabot enabled on the repo |
| Server compromise of the VPS running `crew` | Out of scope for the project itself — see "operational hardening" below |

### Out of scope

- **Supply chain attacks on Python itself, the Linux kernel, or upstream libraries.**
  Patch your base system. See [SETUP.md](./SETUP.md) for hardening recommendations.
- **Anthropic / Telegram / NVD platform compromise.** We can't mitigate these;
  rotate credentials if any of those platforms disclose a breach.
- **The content of LinkedIn / X posts you publish.** You review and edit every
  post before publishing. What you choose to post is your responsibility.
- **Multi-user / multi-tenant scenarios.** `crew` is single-user by design.

## Operational hardening (recommended)

If you're running `crew` on a public VPS, do at minimum:

1. **Run as a non-root user.** The supplied [SETUP.md](./SETUP.md) creates a
   dedicated `bot` user. Don't run `crew` as `root`.
2. **`chmod 600` the `.env` file.** Already documented in setup; double-check.
3. **Disable password SSH.** Key-only authentication on the VPS.
4. **Enable unattended security upgrades.** `unattended-upgrades` on Debian/Ubuntu.
5. **Cap Anthropic spend.** Set a hard monthly limit in
   [console.anthropic.com](https://console.anthropic.com). The default budget
   alerts won't stop a leaked key from billing you €1,000 overnight.
6. **Rotate tokens periodically.** Telegram bot token and Anthropic API key —
   every 6 months minimum, immediately on any suspicion of compromise.
7. **Never commit `.env`.** A `.gitignore` is included that excludes it. Don't
   override it.

## Known weaknesses we accept

- **Prompt injection on signal titles is possible.** A maliciously crafted HN
  title or GitHub repo name could try to steer a draft. We rely on human review
  as the mitigation. Don't ever post a draft without reading it.
- **The GitHub Trending scrape uses a fragile regex.** If GitHub changes their
  HTML, the source silently returns zero results. Other sources continue to
  work. Logged as a warning, not a failure.
- **NVD's API is rate-limited.** Without an API key, you get ~5 requests per
  30 seconds. Fine for daily use; add a free key
  ([request one here](https://nvd.nist.gov/developers/request-an-api-key)) if
  you hit limits.
- **No telemetry, ever.** `crew` makes no network calls beyond the four
  documented in code (Anthropic, Telegram, HN, GitHub, NVD). It does not phone
  home to Fendora or anyone else.

## Cryptography / secrets handling

`crew` does not implement its own cryptography. All credentials are passed via
environment variables and used directly against TLS-protected APIs. No secrets
are written to the SQLite state DB. No secrets are logged.

## Dependencies

| Package | Why | Risk |
|---|---|---|
| `anthropic` | Official SDK for Claude API | Low — first-party SDK |
| `requests` | HTTP client | Low — long-established, well-audited |

That's it. Two runtime dependencies. Every transitive dep is visible in
`requirements.txt` after `pip freeze`.

## Contact

- Security issues: `security@fendora.io`
- Everything else: GitHub issues at `github.com/fendora-io/crew/issues`
