# Changelog

All notable changes to Claude Insight are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the
project aims for [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **Usage & Crabi-tool adoption** report section — entirely additive after `parse()`
  (the scored corpus, fluency score, archetype, and skill map are unchanged):
  - a 7-way **work-type mix** (Build / Debug / Plan / Investigate / Shell-Ops /
    Delegate / Other) over tool actions, with prompts excluded;
  - most-used **MCP servers** and **slash commands** over the measured window;
  - **Crabi marketplace adoption** — per-plugin installed / enabled / used, with usage
    counted across slash-command, MCP, and sub-agent channels and a flag for
    installed-but-never-used tools. Read live and offline from local plugin config.
- `behavior.usage` / `behavior.adoption` in the evidence bundle (outside the run
  fingerprint), plus an `/ai-fluency` coaching nudge that turns an installed-but-unused
  tool into a concrete growth card.
- Continuous integration: the test suite runs on every push to `main` and every
  pull request, across Python 3.8 / 3.10 / 3.12. Nothing merges red.
- `LICENSE` file (MIT) — the README already declared MIT; this makes it real.
- This changelog.

### Changed
- The installer now downloads the **latest tagged release** instead of bleeding-edge
  `main`, so a work-in-progress commit on `main` can never break a fresh install.
  It falls back to `main` only if no release exists.

### Removed
- The in-report **"Methodology & honesty" appendix** and the **"Why only ~N days?"** /
  **"The honest part"** blocks. The de-contamination still runs exactly as before — only
  the in-report display of those breakdowns was removed.

## [1.0.0] — 2026-06-19

First tagged release — the known-good baseline existing users can pin to.

### Added
- Single-file, pure-stdlib engine (`insight.py`): discover → de-contaminate →
  score → report.
- `/ai-fluency` skill and the Sonnet 4.6 → Opus 4.8 workflow.
- 0–100 fluency score, builder archetype, 4-competency skill map, five measured
  dimensions, and personalized growth levers.
- Built-in private archive so analysis can see beyond Claude Code's 30-day window.
- 38 passing tests.

[Unreleased]: https://github.com/Feloguarin/claude-insight/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Feloguarin/claude-insight/releases/tag/v1.0.0
