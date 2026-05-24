# Contributing

`crew` is intentionally small (one Python file, two dependencies, single-user
CLI). PRs that fit that design are welcome; PRs that grow it into a platform
will be politely declined.

## Welcome

- **New signal sources** — Reddit (r/devops, r/kubernetes, r/netsec), GitHub
  Security Advisories, vendor blogs (Snyk, Wiz, Datadog Security Labs), CNCF
  security bulletins. Each new source: one function returning the standard
  signal dict shape, wired into `gather_signals`.
- **Better dedup / scoring logic** — current ranking is naive (CVEs > HN by
  engagement > GitHub). Data-driven improvements very welcome once we have
  posting data.
- **Bug fixes** — especially around the GitHub Trending scrape, which is fragile
  by design.
- **Voice prompt improvements** — banned words, length tuning, structural rules.
  Note these are mostly subjective; expect discussion.
- **Documentation** — clearer setup instructions, screenshots, troubleshooting.

## Not welcome

- **Posting integrations** (Typefully, Buffer, native LinkedIn/X APIs). Manual
  posting is a feature: it forces you to read each draft before it goes out.
- **Web UI, dashboards, multi-tenant.** Single-user CLI is the design.
- **"AI agent" framework rewrites** (LangChain, CrewAI, AutoGen, etc.). The
  whole thing is one Python file. It should stay that way.
- **Webhook receivers, schedulers, queues.** Cron is sufficient.
- **Telemetry, analytics, "anonymous usage data".** Hard no.

## How to propose a change

1. Open an issue describing what you want to change and why. For anything
   non-trivial, get feedback on the design before writing code.
2. Fork, branch, implement.
3. PR with a clear title, a description of what changed and why, and (if it's
   a new signal source) an example of the output.

## Code style

- Plain Python 3.10+, standard library where possible.
- No new runtime dependencies without strong justification.
- Type hints on function signatures.
- Black / Ruff formatting if you have them; not enforced.
- No tests yet — the project is too small. If you add a non-trivial feature,
  add a minimal test for it.

## Security

If you've found a security issue, **do not open a public issue or PR**.
See [SECURITY.md](./SECURITY.md) for the disclosure process.

## License

By contributing, you agree your contributions are licensed under the
[MIT License](./LICENSE).
