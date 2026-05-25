# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/fendora-io/crew/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/fendora-io/crew/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/fendora-io/crew/releases/tag/v0.1.0
