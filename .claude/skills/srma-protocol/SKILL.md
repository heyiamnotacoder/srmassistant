---
name: srma-protocol
description: Develop a systematic review protocol from a research question — sharpen the question, force every eligibility and methods decision through a structured checklist, run a scoping search for feasibility, and emit a paste-ready PROSPERO registration draft plus machine-readable pico.json and screening criteria. Use when the user is starting a systematic review / meta-analysis, has a research question but no registered protocol, or wants help registering on PROSPERO. Runs before screening and extraction.
---

# SRMA Protocol Builder — Stage 0 (Claude Code adapter)

The canonical workflow lives in `prompts/protocol-builder.md` at the project root, and the PROSPERO field
authority in `prompts/reference/prospero-fields.md`. **Read both first and execute the workflow.** This
adapter only adds Claude Code mechanics.

This stage runs **before** `/srma-screen` and `/srma-extract`. If the user already has a registered
PROSPERO, skip this stage — record `protocol/registration.json` and go straight to `/srma-screen`.

## Mechanics

- **Phase P-A (sharpen the question)** — conversational. Use AskUserQuestion for the review-type choice when
  the question is ambiguous between types; it changes every downstream default.

- **Phase P-B (decision checklist)** — the heart of the stage, and the part to not rush. Work through the
  checklist groups in order (Population → Intervention → Comparator → Study design → Context/limits →
  Outcomes). Batch related items into AskUserQuestion calls of 2–4 questions rather than one question per
  item, and always lead with a recommended default so the user is accepting or overriding rather than
  composing from scratch. Track answered vs outstanding items with TodoWrite — an unanswered item is a
  future amendment, so none may be silently dropped.

- **Phase P-C (scoping search)** — this session has literature tools; use them rather than asking the user
  to run searches by hand:
  - `mcp__claude_ai_PubMed__search_articles` for yield counts per concept block and per restriction. Report
    **counts and design mix**, not candidate study lists.
  - `mcp__claude_ai_Clinical_Trials__search_trials` for ongoing/unpublished trials worth noting.
  - For the `Check for similar records already in PROSPERO` field, search the register itself. It is a JS
    single-page app, so WebFetch returns an empty shell — drive it with Playwright per the user's
    `playwright-web-check` skill (global install at `/opt/homebrew/lib/node_modules/playwright`; import the
    CommonJS default export, navigate with `waitUntil: "domcontentloaded"` plus a wait, not `networkidle`).
    Records render at `https://www.crd.york.ac.uk/PROSPERO/view/<CRD-number>`.
  - If a tool is unavailable, hand the user the search strings and take their counts — never fabricate a yield.

- **Phase P-D (methods)** — same AskUserQuestion pattern, defaults matched to the review type (RoB 2 for
  RCTs, ROBINS-I for non-randomised interventions, QUADAS-2 for diagnostic accuracy, QUIPS for prognosis).

- **Phase P-E (emit)** — write `protocol/pico.json`, `protocol/prospero_draft.md`, and
  `screening/criteria.json` with the Write tool. Generate the draft against
  `prompts/reference/prospero-fields.md`, marking every field **free / pick / struct / auto**. Put each
  free-text answer in its own fenced block so it can be copied cleanly, and quote each pick-list option
  exactly as PROSPERO words it. Publishing the draft as an Artifact is a good option when the user wants to
  work through it away from the terminal — offer it, don't assume it.

- **Phase P-F (register)** — the user registers; PROSPERO needs a login, so this is theirs to do. Suggest
  they run it via `! open https://www.crd.york.ac.uk/prospero/`. When they report the CRD number, write
  `protocol/registration.json`.

## Rules

Everything in `prompts/protocol-builder.md` applies verbatim — in particular: confirm decisions before
drafting, mark unfillable fields `⚠ NEEDS INPUT` rather than inventing content, never tune criteria to
change which studies survive, and never tick the review-stage matrix for work that has not happened.
