# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] — 2026-06-01

### Fixed
- `check_replies()` now replies to the exact chat and thread the message came from,
  instead of always posting to the hardcoded `TELEGRAM_THREAD_ID`. Silent mismatch
  when groups use topics caused `skip`/`done` acks to go to the wrong thread.
- Telegram API errors in reply acks now log to stderr and surface in `/var/log/crew.log`.
- Preflight card formatting: `post_risk` normalized to a single word (was sometimes
  "medium — explanation"), factual flags rendered as individual bullet lines, em dash
  ban extended to preflight JSON fields.

## [0.2.0] — 2026-05-31

### Added
- `crew.toml` config file — add/remove keywords and topics without touching `crew.py`.
  Supports `keywords.include`, `keywords.exclude`, `keywords.cve_products`, `keywords.hn_fallback_topics`.
- Pre-flight critical analysis on every draft: Claude flags recency, factual risks, and
  audience fit before the post is shown. Displayed as a colour-coded block in Telegram.
- EU regulatory keywords out of the box: CRA, NIS2, DORA, EU AI Act, SBOM, secure-by-design.
- Exclude keyword list to drop off-topic stories (sustainability, grid, nuclear, layoffs).

### Fixed
- Day-aware CTA: posts now use the correct weekday ("Sunday check:", "Wednesday check:")
  instead of always saying "Monday".
- Banned stale time references ("X days ago", "recently", "just launched") in voice prompt
  so Claude reframes around topic/version rather than echoing source article timelines.
- Malformed `crew.toml` now prints a warning and falls back to defaults instead of crashing.
- Intentional empty keyword list in `crew.toml` is now respected (was silently ignored).
- Exclude filter now applies to all sources (HN, GitHub Trending, CVEs), not just HN.

## [0.1.1] — 2026-05-25

### Fixed
- HN fetch now restricted to last 24h via `created_at_i` filter — old stories
  resurfacing on the front page no longer waste Claude API tokens.
- Fallback topic search switched to `search_by_date` endpoint for recency-sorted results.

## [0.1.0] — 2026-05-24

### Added
- Initial release.
- Signal sources: Hacker News, GitHub Trending, NVD CVE feed.
- Claude-based draft generation (LinkedIn post + X thread + hook).
- Telegram digest with copy-paste-ready code blocks.
- SQLite-based dedup across runs.
- `done` / `skip` reply acknowledgments.
- Anthropic prompt caching on the static voice prefix.
- GitHub Actions CI (lint + secret scan).
- Dependabot config for `pip` and `github-actions`.
- Issue templates and PR template.
- SECURITY.md with threat model and disclosure process.

[Unreleased]: https://github.com/fendora-io/crew/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/fendora-io/crew/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/fendora-io/crew/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/fendora-io/crew/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/fendora-io/crew/releases/tag/v0.1.0
