---
date: 2026-06-21
planner: Angel Rodriguez
git_commit: 03588b6285b55774e243f7d68ebc7fdd159bd55a
branch: main
repository: claude-insights
topic: "Score-first AI-fluency report redesign + 3 new provenance/adoption fields (evaluated date, Claude Code version, two-section plugin adoption)"
status: ready
autonomy: verbose
commit_per_phase: true
based_on: thoughts/arodriguez/research/2026-06-21-ai-fluency-report-redesign.md
last_updated: 2026-06-21
last_updated_by: phase-running (Phase 4)
---

# AI-Fluency Report Redesign + New Provenance Fields — Implementation Plan

## Overview

Two coupled changes to the single-file `insight.py` report generator:

1. **Restructure** the report from 12 scattered sections into the **5 question-driven groups** specced in the research doc (score-first arc), then **restyle** the HTML per the frontend-design findings.
2. **Add new fields**: the **evaluated date** (+ activity window), the **Claude Code version**, and a **two-section plugin adoption** view — *Crabi suggested plugins* (engram, obsidian, ponytail, desplega toolbox, superpowers) and *Crabi AI marketplace* (each catalog plugin) — each plugin showing **installed / used / outdated** status (outdated = installed version behind the latest the local marketplace clone offers).
3. **Documentation** (Phase 4): bring `README.md`, the example screenshot, and `CHANGELOG.md` in line with the redesign and the new fields.

- **Motivation**: The current report order violates basic report-structuring principles (research doc). Separately, the user wants provenance (when the report was generated, which CC version) and a complete per-plugin marketplace adoption picture.
- **Related**:
  - Research / spec: `thoughts/arodriguez/research/2026-06-21-ai-fluency-report-redesign.md`
  - `insight.py` — single-file tool that emits the report
  - Prior: `thoughts/arodriguez/plans/2026-06-21-usage-analytics-crabi-adoption.md` (shipped the §7 usage/adoption panel)

## Current State Analysis

The whole report is one f-string in `build_html()` (`insight.py:1626`), with sub-builders `_analysis_section_html()` (`insight.py:1327`) and `_usage_section_html()` (`insight.py:1380`). Current 12-section order: `insight.py:1915–2002`; `<style>` block: `insight.py:1827–1912`. Single call site: `insight.py:2207`.

Data availability for the three new fields (verified on this machine):

| Field | Captured today? | Source (verified) | Threading |
|-------|-----------------|-------------------|-----------|
| **Evaluated date** | No — `datetime.now()` is never called (`datetime` imported at `insight.py:44`). Only `corpus.first_ts`/`last_ts` exist (`insight.py:615–616`, set `749–753`). Footer (`insight.py:2002`) is a static string. | Generate at run time; activity window from `first_ts`/`last_ts`; `days` already computed at `insight.py:1642`. | `corpus` already in `build_html`; add an optional `generated_at` param (testability seam). |
| **Claude Code version** | No — parse loop (`insight.py:741–816`) never reads `version`. `Corpus` has no version field. | Transcripts carry a top-level per-event `version` (confirmed: `2.1.185` in 36/50 events of the newest transcript). | New `Corpus.cc_version` field + one capture line in parse; `build_html` reads `corpus.cc_version` (no new param). |
| **Two-section plugin adoption** | **Partially.** `build_adoption()` (`insight.py:514`) already returns the `crabi/ai-marketplace` target with a `plugin_breakdown` (name/used/enabled, **installed-only**), rendered at `insight.py:1457–1470`, plus aggregate named-tool targets (engram, ponytail, obsidian, desplega) at `insight.py:558–577`. `SIGNATURES` (`insight.py:414–438`) has **no superpowers** entry. | Full Crabi catalog is on disk: `<installLocation>/.claude-plugin/marketplace.json` (10 plugins; `infra` is **not installed** — a real not-installed case). `installLocation` is in `known_marketplaces.json`. | `adoption` already threaded end-to-end. Extend `build_adoption` (catalog read + superpowers signature); split rendering in `_usage_section_html`. |

**Verified facts that shape the plan:**
- Crabi catalog (10): `breaking-balls-reviewer, database, frontend, backend, qa, infra, data, docs, sre, security-guards`. Installed: all except `infra`.
- `superpowers` is **not installed** and has no marketplace entry → in "suggested plugins" it shows *not installed* (the coaching point). Its `plugin_id`/usage signature is **best-effort** until installed.
- **Outdated detection is feasible**: installed version = `installed_plugins.json` → `plugins[id][0]["version"]`; latest = the marketplace clone's `.claude-plugin/marketplace.json` → `plugins[].version`. Verified live: **engram is outdated** (installed `0.1.0` < latest `0.1.1`); all installed Crabi plugins are current; `ponytail`/`desplega` catalog entries carry **no version**, and many official plugins record `"version": "unknown"` → those must render *unknown*, never a false up-to-date/outdated claim.
- Test harness: pure-stdlib `unittest`; helpers `write_session`, `user_text` (forwards `**extra` to top-level event keys → can inject `version`), `assistant_tool`, `_write_claude_config` (writes fake `installed_plugins.json` / `known_marketplaces.json` / `settings.json`). CI gate: `python3 -m unittest discover -s tests`.

## Desired End State

Running `python3 insight.py <transcripts> -o report.html` produces a report that:
1. Opens score-first and flows through the 5 groups (verdict → why → standing → what-now → trust/method), per the research spec.
2. Shows, in a header meta line **and** the footer: the **evaluated date**, the **activity window** (`first → last (N days)`), and the **Claude Code version**.
3. In Group 5, renders **two** adoption sub-sections: *Crabi suggested plugins* (per tool incl. superpowers as not-installed) and *Crabi AI marketplace* (every catalog plugin). Each plugin is tagged not-installed / installed-idle / installed-used **and** carries an **outdated** marker (`update available · vX → vY`) when its installed version trails the catalog's latest; *unknown* when versions can't be compared.
4. Still renders cleanly in the deterministic-only fallback (no Opus analysis) and when config/catalog/version files are missing.
5. Visual craft per the research: single hero ring, bullet-style dimension bars, label+color (not color-alone) quality encoding, lifted dark surface, 8-pt spacing, modular type scale.

Verify: existing suite stays green; new unit tests cover version capture, generated_at rendering, full-catalog adoption, and outdated detection; a headless screenshot confirms the 5-group order + new fields.

## What We're NOT Doing

- **Not** fixing the pre-existing tz-comparison crash in `parse()` (`insight.py:505`) that breaks runs over the real `~/.claude` (offset-naive vs offset-aware compare). Out of scope; verification uses fixtures. *(Derail note — track separately.)*
- **Not** adding a network call to fetch the marketplace catalog — read the already-cloned local manifest only.
- **Not** adding the optional "shareable summary card" from the research's open questions (out of scope unless requested).
- **Not** changing the scoring/analysis math, the archive logic, or the evidence-pipeline schema.
- **Not** introducing a template engine or any new dependency (stays pure stdlib).

## Implementation Approach

- **Phase 1 — Data plumbing (backend only, no visual change).** Capture CC version; add the `generated_at` seam; add the `superpowers` signature; extend `build_adoption` to emit a full-catalog per-plugin breakdown for the Crabi marketplace **with per-plugin installed/latest versions + an `outdated` flag** (best-effort manifest read, graceful fallback to installed-only). Fully unit-testable.
- **Phase 2 — Restructure + render new fields.** Reorder the `build_html` f-string into the 5 groups; render the evaluated-date/window/version meta line (header) + footer; split `_usage_section_html` into the two adoption sub-sections, each showing per-plugin status + outdated markers. Preserve the no-analysis fallback.
- **Phase 3 — Visual restyle (independent polish).** Apply the frontend-design changes (ring/bars/color/surface/spacing/type). Separable: Phases 1–2 already deliver the new structure + all new fields; Phase 3 can ship after.
- **Phase 4 — Documentation + installation.** Update `README.md` (features, example output, adoption section, install review), regenerate the example screenshot, and add the `CHANGELOG.md` entry. Last, so docs reflect the final shipped report.
- **Sequencing rationale:** data before rendering before styling before docs — each phase is independently verifiable, and a regression in one layer can't be masked by another.

## Quick Verification Reference

- Run on a fixture: `python3 insight.py <fixture-dir> -o /tmp/out.html --no-open` (exit 0)
- Full suite: `python3 -m unittest discover -s tests`
- Single module while iterating: `python3 -m unittest tests.test_insight -v`
- Headless screenshot of `/tmp/out.html` via the Playwright MCP for the layout QA

---

## Phase 1: Data plumbing for the three new fields

### Overview

Backend-only changes so the new fields exist in the data model before any rendering: `corpus.cc_version`, a `generated_at` seam on `build_html`, a `superpowers` signature, and a full-catalog `plugin_breakdown` for the Crabi marketplace carrying per-plugin installed/latest versions + an `outdated` flag (and the same version/outdated data on suggested tools). No visible report change yet.

### Changes Required:

#### 1. Capture Claude Code version
**File**: `insight.py`
**Changes**:
- Add `self.cc_version = None` to `Corpus.__init__` (near `insight.py:615`).
- In the parse loop (`insight.py:~749`, where `ts` is parsed), read `v = e.get("version")`; keep the version from the **latest event that actually carries a `version`** (track a separate "latest-ts-with-version" alongside `last_ts` — do **not** just read the version off the max-ts event, since ~28% of events have no `version` and the last event may be one of them, which would leave `cc_version` `None` despite versions being present).

#### 2. `generated_at` testability seam
**File**: `insight.py`
**Changes**:
- Add `generated_at=None` to the `build_html(...)` signature (`insight.py:1626`); inside, `generated_at = generated_at or datetime.now()`.
- `main()` call site (`insight.py:2207`) passes nothing (defaults to now). No behavior change for the real run; tests pass a fixed datetime.
- (No rendering yet — Phase 2 consumes it.)

#### 3. `superpowers` signature + outdated detection for suggested tools
**File**: `insight.py`
**Changes**:
- Add a `superpowers` entry to `SIGNATURES` (`insight.py:414`): best-effort `plugin_id` (e.g. `superpowers@superpowers`) + a usage signature (namespace `superpowers:` and/or known skill commands). Mark with a `# ponytail:` comment that the install key is a best-effort guess until the plugin is actually installed.
- Add a pure-stdlib helper `_version_outdated(installed, latest)` → `True`/`False`/`None`: parse both as dotted-int tuples and compare; return `None` (unknown) if either is missing, `"unknown"`, or unparseable. `# ponytail: naive dotted-int compare, no prerelease/semver-build handling — fine for plugin versions`.
- Extend the named-tool loop (`build_adoption`, `insight.py:558–577`) so each suggested-tool entry also carries `installed_version` (read directly off the install record returned by `_load_installed_plugins` — `installed[pid].get("version")`; no new reader needed), `latest_version`, and `outdated` (= `_version_outdated(installed, latest)`). To get `latest_version`, derive the marketplace **name** from the signature's `plugin_id` suffix (`<plugin>@<name>`) and load that marketplace's catalog **by name** (see #4 loader) — a suggested tool only knows its marketplace name, not a repo slug.

#### 4. Full-catalog marketplace breakdown + per-plugin versions
**File**: `insight.py`
**Changes**:
- Add a helper `_load_marketplace_catalog(marketplace=None, repo_slug=None, claude_dir=None)` that resolves a marketplace **either by name** (direct key in `known_marketplaces.json`, which is keyed by name — `insight.py:392`) **or by repo slug** (the entry whose `source.repo == repo_slug` — used for the Crabi target via `CRABI_REPO`), reads its `installLocation` (fallback: `<root>/plugins/marketplaces/<name>`) + `.claude-plugin/marketplace.json`, and returns a **`{plugin_name: latest_version}`** map (version may be `None`). Returns `{}` on any miss (best-effort, never raises).
- Installed version per plugin is **already available** — `_load_installed_plugins` (`insight.py:375–389`) returns the first install-record dict, so read `installed[pid].get("version")`. No new reader needed.
- In `build_adoption` (`insight.py:543–555`), build `plugin_breakdown` over the **union of catalog names + installed crabi plugins**. Each entry: `{"name", "installed": bool, "enabled": bool|None, "used": int, "installed_version", "latest_version", "outdated": bool|None}` (uses existing `_plugin_used` + `_version_outdated`). **Additive**: keep the existing `name`/`used`/`enabled` keys so current tests pass; add the new keys. If the catalog read returns `{}`, fall back to the current installed-only behavior unchanged.

### Success Criteria:

#### Automated Verification:
- [ ] Full suite passes: `python3 -m unittest discover -s tests`
- [ ] New test — version capture (latest-with-version wins): `python3 -m unittest tests.test_insight.TestVersionCapture -v` — feed two `user_text(..., version=...)` events with different timestamps; assert `corpus.cc_version` is the later one; assert `None` when no `version` key present; **and** when the latest-timestamp event has *no* `version` but an earlier one does, assert `cc_version` is the earlier (non-None) version.
- [ ] New test — full-catalog adoption: `python3 -m unittest tests.test_insight.TestAdoption -v` — extend `_write_claude_config` to write a fake `marketplaces/<name>/.claude-plugin/marketplace.json`; assert `plugin_breakdown` includes a **not-installed** catalog plugin (`installed=False, used=0`) and an installed one (`installed=True`); missing-manifest falls back to installed-only without error.
- [ ] New test — outdated detection: `python3 -m unittest tests.test_insight.TestOutdated -v` — `_version_outdated("0.1.0","0.1.1")` is `True`, equal is `False`, and `"unknown"`/`None`/unparseable is `None`; a breakdown entry whose installed < latest carries `outdated=True`.
- [ ] Backward-compat: `TestAdoption.test_adoption_crabi_plugin_breakdown` still passes unchanged (breakdown keys `name`/`used` intact).

#### Automated QA:
- [ ] Run `python3 insight.py <fixture-dir> --json --no-open` and confirm the emitted metrics include a non-null `cc_version` (when the fixture events carry `version`) and the adoption block carries the enriched `plugin_breakdown` (with `installed_version` / `latest_version` / `outdated`).

#### Manual Verification:
- [ ] None required — all behavior is unit-testable.

**Implementation Note**: After this phase, pause for manual confirmation. Commit-per-phase enabled → commit `[phase 1] data plumbing: cc_version, generated_at seam, superpowers signature, full-catalog + outdated adoption` after verification passes.

---

## Phase 2: Restructure into 5 groups + render the new fields

### Overview

Reorder `build_html`'s body into the 5 question-driven groups and surface the three new fields: an evaluated-date/window/version meta line in the header + footer, and a two-section adoption view (suggested plugins / marketplace catalog) in Group 5. No visual-craft restyle yet (Phase 3).

### Changes Required:

#### 1. Regroup the body markup
**File**: `insight.py` (`build_html`, `1915–2002`)
**Changes**: Reorder the existing f-string blocks into Groups 1–5 per the research spec (§"Recommended regrouping"):
- **G1 Verdict**: title strip → score ring → band + band-meaning (co-located, fixes the §3/§5 split) → archetype.
- **G2 Why**: assessment prose → AI skill-map analysis → five dimensions.
- **G3 Standing**: strength callout → unified L1–L5 skill map → archetype affinity (`<details>`).
- **G4 What now**: improvement/growth cards (moved to the climax).
- **G5 Trust & method** (`<details>`): ingest tiles → **two** adoption sub-sections → honest-numbers facts.
- Keep the no-analysis fallback intact (`analysis_status_html`, `insight.py:1634`); Group 2's analysis block may be absent.

#### 2. Evaluated-date / window / version meta line + footer
**File**: `insight.py`
**Changes**:
- Header meta line (under the G1 title strip): `Evaluated {generated_at:%Y-%m-%d} · Claude Code v{corpus.cc_version or '—'} · activity {first:%Y-%m-%d} → {last:%Y-%m-%d} ({days} days)`.
- **Guard the activity-window segment**: when `corpus.first_ts`/`last_ts` is `None` (timestamp-less corpus), omit the `activity … ({days} days)` part entirely — never format a `None` with `%Y-%m-%d`. Reuse the existing `if corpus.first_ts and corpus.last_ts` guard pattern (`insight.py:1642`). The evaluated-date + version segments always render. (Satisfies Desired-End-State #4.)
- Augment the footer (`insight.py:2002`) with the same evaluated date + CC version.

#### 3. Split the adoption rendering into two sub-sections
**File**: `insight.py` (`_usage_section_html`, `1432–1477`)
**Changes**:
- **Crabi suggested plugins**: the named-tool targets (engram, ponytail, obsidian, desplega, superpowers) as aggregate installed/used badge rows (superpowers → not-installed), each with an **outdated** marker when `outdated` is true.
- **Crabi AI marketplace**: iterate the enriched `plugin_breakdown`, rendering **each** catalog plugin with a status tag: *not installed* / *installed · idle* / *installed · used N×*, plus an **outdated** badge (`update available · vX → vY`) when `outdated` is true. Pair every status with a label (not color alone — sets up Phase 3). When `outdated` is `None`, render no version claim.

### Success Criteria:

#### Automated Verification:
- [x] Full suite passes: `python3 -m unittest discover -s tests`
- [x] Existing render guards still pass: `TestEndToEnd.test_full_run_and_html`, `TestPipelineModes`, `TestUsageSectionHtml`, the fallback tests (`test_report_without_analysis_has_no_ai_section`, `test_real_prompts_but_zero_tool_calls_renders`).
- [x] New test — meta line renders: `python3 -m unittest tests.test_insight.TestMetaLine -v` — pass a fixed `generated_at` + a corpus with `cc_version` set; assert the date, `Claude Code v…`, and the activity-window range appear in the HTML; **and** a corpus with `first_ts`/`last_ts` `None` renders the meta line (date + version) without crashing and without the activity-window segment.
- [x] New test — two adoption sub-sections: `python3 -m unittest tests.test_insight.TestTwoSectionAdoption -v` — assert both "suggested plugins" and "marketplace" headings render, a not-installed catalog plugin shows a "not installed" label, superpowers appears as not-installed, and a plugin with `outdated=True` renders the `update available` / `vX → vY` marker (while an `outdated=None` plugin shows no version claim).

#### Automated QA:
- [x] Render a fixture report and open `/tmp/out.html` headless (Playwright MCP); confirm section order is verdict → why → standing → what-now → trust, the meta line is visible near the title, and the two adoption sub-sections appear under Group 5. Capture a screenshot.

#### Manual Verification:
- [ ] Eyeball the screenshot: groups read in the intended order and the new fields are legible.

**Implementation Note**: After this phase, pause for manual confirmation. Commit `[phase 2] regroup into 5 groups + render evaluated date / CC version / two-section adoption with outdated markers` after verification passes.

### QA Spec (optional):

Reserved — a cross-cutting visual QA doc covering the full before/after of the redesign is better produced once Phase 3 lands. Generate via `desplega:qa` at handoff if desired: `thoughts/arodriguez/qa/2026-06-21-ai-fluency-report-redesign.md`.

---

## Phase 3: Visual restyle (frontend-design)

### Overview

Apply the research's prioritized visual changes to the `<style>` block (`insight.py:1827–1912`) and the relevant markup: single hero ring, bullet-style dimension bars, label+color quality encoding, lifted dark surface, 8-pt spacing scale, modular type scale, stripped non-data ink. Pure presentation — no data or structural change.

### Changes Required:

#### 1. Palette + surface
**File**: `insight.py` (`<style>`, `1827–1912`)
**Changes**: Lift base `#0c0d18` → ~`#121214`; desaturate `#7c5cff`/`#3ad6c9` for text/small marks; signal elevation by lightness; verify 4.5:1 (WCAG AA).

#### 2. Data-viz encodings
**File**: `insight.py` (dimension bars + dot scales + score ring markup/CSS)
**Changes**: Keep one hero ring only; convert the five dimension bars to bullet style (target marker + faint band); replace color-only / red-green quality with a blue↔orange (or sequential) ramp **plus** a label/icon on every bar, dot scale, and tile.

#### 3. Spacing + type
**File**: `insight.py` (`<style>`)
**Changes**: 8-pt spacing (internal ≤ external); lock ~4 heading + 2 body sizes on a 1.25/1.333 scale; body 16–18px / lh 1.5; differentiate by weight/opacity; strip gridlines/glows/tick rings/3D.

### Success Criteria:

#### Automated Verification:
- [x] Full suite still passes (no string assertions should break — restyle must not remove the marker strings tests check for): `python3 -m unittest discover -s tests`

#### Automated QA:
- [x] Headless screenshot of a fixture report (Playwright MCP); confirm a single ring, bullet-style dimension bars, label+color encoding, and the lifted surface. Capture before/after screenshots.
- [x] Run a programmatic contrast check (or a scripted assertion) on the primary text/accent pairs to confirm ≥ 4.5:1.

#### Manual Verification:
- [ ] Visual judgment on the screenshot: hierarchy reads correctly, no optical vibration, grayscale-legible (quality not conveyed by color alone).

**Implementation Note**: After this phase, pause for manual confirmation. Commit `[phase 3] visual restyle: ring/bullet-bars/color-encoding/surface/spacing/type` after verification passes.

---

## Phase 4: Documentation + installation

### Overview

Bring the user-facing docs in line with the redesigned report and new fields: update `README.md` (features, example output, adoption section, install section), regenerate the example screenshot, and add a `CHANGELOG.md` entry. No install **mechanics** change — every change lives in `insight.py`, which `install.sh` already copies — so this phase confirms install instructions still hold and refreshes the prose, rather than altering the installer.

### Changes Required:

#### 1. README feature + output docs
**File**: `README.md`
**Changes**:
- "## 🚀 What you get" (`README.md:34`) and "## 📊 Example output" (`README.md:152–166`): describe the new **5-group score-first structure** and the **evaluated date / activity window / Claude Code version** meta line.
- "### Usage & Crabi-tool adoption" (`README.md:202–214`): rewrite to document the **two** sub-sections — *Crabi suggested plugins* (engram, obsidian, ponytail, desplega, superpowers — aggregate) and *Crabi AI marketplace* (each catalog plugin: not-installed / installed-idle / installed-used) — and the per-plugin **outdated** marker (installed version vs. latest, *unknown* when not comparable).

#### 2. Example screenshot
**File**: `render-full.png` (repo root; currently untracked)
**Changes**: Regenerate from a representative fixture run so the embedded/example image reflects the redesigned report. Commit the refreshed image if the README references it.

#### 3. Install section review
**File**: `README.md` ("## ⚡ Install in 5 seconds", `README.md:11`) and `install.sh`
**Changes**: Confirm the install steps and the `install.sh` copy-list (`insight.py`, framework, `SKILL.md`, workflow) still cover everything the redesign needs (expected: unchanged — no new files). Update the install prose only if a gap is found; otherwise note "no change required."

#### 4. Changelog
**File**: `CHANGELOG.md`
**Changes**: Under `## [Unreleased]`, add **Changed** (report regrouped into 5 score-first groups; visual restyle) and **Added** (evaluated date + activity window + Claude Code version in the report; two-section plugin adoption with full Crabi marketplace catalog incl. not-installed; superpowers as a suggested tool; per-plugin **outdated** detection — installed vs. latest catalog version).

### Success Criteria:

#### Automated Verification:
- [x] Test suite still green (docs must not break the gate): `python3 -m unittest discover -s tests`
- [x] No broken relative links / stale section names in README: `grep -n "Usage & Crabi-tool adoption\|Example output\|Install in 5 seconds" README.md` returns the expected (updated) headings.
- [x] CHANGELOG has the new entries under Unreleased: `grep -n -A2 "## \[Unreleased\]" CHANGELOG.md`

#### Automated QA:
- [x] Render a fixture report and confirm its actual structure/fields match what the README now claims (regroup order, meta line, two adoption sub-sections); regenerate `render-full.png` from that run.

#### Manual Verification:
- [ ] Read-through of the updated README: feature descriptions, example output, and the adoption section accurately describe the shipped report; the screenshot matches.

**Implementation Note**: After this phase, pause for manual confirmation. Commit `[phase 4] docs: README + example screenshot + changelog for the redesign & new fields` after verification passes.

---

## Appendix

- **Follow-up / split point**: Phase 3 is independent polish — if it grows beyond one session, split it into its own plan; Phases 1–2 already deliver the structure + all new fields. Phase 4 (docs) always runs last.
- **Derail notes**:
  - Pre-existing tz-comparison crash in `parse()` (`insight.py:505`) when transcript timestamps mix tz formats — blocks running over real `~/.claude`; track separately.
  - `superpowers` install key is a best-effort guess until the plugin is installed; revisit the signature once it appears in `installed_plugins.json`.
  - **"Latest" = the locally-cloned marketplace's version**, which is only as fresh as the last marketplace sync (`known_marketplaces.json` `lastUpdated` / `autoUpdate`). "Outdated" is therefore relative to that local clone, not the true upstream — acceptable and offline-honest, but worth stating in the report copy.
- **References**:
  - Research: `thoughts/arodriguez/research/2026-06-21-ai-fluency-report-redesign.md`
  - Prior plan: `thoughts/arodriguez/plans/2026-06-21-usage-analytics-crabi-adoption.md`
  - Test harness: `tests/test_insight.py` (helpers + `TestAdoption`, `TestUsageSectionHtml`)

---

## Review Errata

_Reviewed: 2026-06-21 by Angel Rodriguez (desplega:review, auto-apply mode). Structure: PASS. Line references spot-checked against `insight.py` — all confirmed except the one noted below. No Critical findings._

### Applied (Important)
- [x] **CC-version capture correctness** (Phase 1 #1) — spec now tracks the latest event *that carries a `version`*, not the max-ts event (≈28% of events lack `version`), so `cc_version` can't go `None` when versions exist. Locked by an extra `TestVersionCapture` assertion.
- [x] **Meta-line `None`-timestamp guard** (Phase 2 #2) — spec now omits the activity-window segment when `first_ts`/`last_ts` is `None`, reusing the `insight.py:1642` guard. Locked by an extra `TestMetaLine` assertion.
- [x] **Suggested-tool latest-version resolution** (Phase 1 #3/#4) — `_load_marketplace_catalog` now resolves a marketplace by **name** (for suggested tools, derived from the `plugin_id` suffix) or by repo slug (for the Crabi target); path made explicit.

### Applied (Minor)
- [x] `_analysis_section_html` line ref corrected `1332` → **`1327`** (Current State).
- [x] Phase 1 #4 no longer claims a new installed-version reader is needed — `_load_installed_plugins` (`insight.py:375–389`) already returns the record dict with `version`.

### Noted, not changed
- Phases 2 and 3 both touch the `build_html` body/CSS — keep them in their separate planned commits so a restyle regression can't mask a regroup regression. The plan already flags Phase 3 as separable; no change needed.
