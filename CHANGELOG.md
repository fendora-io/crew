# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.4] — 2026-06-27

### Fixed
- GitHub Trending scraper broken since GitHub changed repo links from
  `<h2 class="h3 lh-condensed">` to `<article class="Box-row">` elements.
  Scraper now matches `<article>` tags and skips `/sponsors/` hrefs.
- HN fallback topic search was using the same 50-point threshold as the
  front-page search, dropping all results. Fallback now defaults to 5 points
  (`CREW_HN_FALLBACK_MIN_POINTS` env var to override).

## [0.2.3] — 2026-06-23

### Fixed
- HN Algolia API stopped supporting `points` as a numeric filter around June 18,
  silently returning 0 results and causing every daily run to report "No fresh signals".
  Points threshold is now applied client-side after fetching.

## [0.2.2] — 2026-06-04

### Fixed
- `tg_send` now handles Telegram HTTP 429 rate-limit responses with automatic
  back-off (`sleep(retry_after)`), up to 4 attempts. Silent drops were causing
  the 3rd signal to vanish when the group hit ~20 msg/min. Errors now log to stderr.
- `check_replies` only responds to messages that are explicit replies to the bot.
  Previously any message containing `skip` in the group triggered an ack.
- Day CTA instruction moved to end of prompt as a `CRITICAL` line; fixes LLM
  occasionally writing the wrong weekday in CTAs.

### Changed
- `anthropic` SDK bumped from `>=0.104.1` to `>=0.105.2`.

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

[Unreleased]: https://github.com/fendora-io/crew/compare/v0.2.2...HEAD
[0.2.2]: https://github.com/fendora-io/crew/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/fendora-io/crew/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/fendora-io/crew/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/fendora-io/crew/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/fendora-io/crew/releases/tag/v0.1.0
