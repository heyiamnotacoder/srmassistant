# SRMA Protocol Builder (Stage 0)

Canonical workflow for turning a research question into a complete, registrable review protocol. This is
the **first** stage — it runs before screening (`prompts/screening-orchestrator.md`) and before extraction
(`prompts/orchestrator.md`). Tool-agnostic: any capable LLM in any harness. Vendor adapters add mechanics
only; this file is the source of truth.

**Why this stage exists.** Nobody starts a review holding a finished PROSPERO registration. They start
holding a question. The registration is the *output* of protocol development, not its input. The job here
is to make every eligibility and methods decision explicitly, informed by what the literature actually
looks like, so the registration is complete the first time and amendments stay rare.

**What it produces:**

| Artifact | Purpose |
|---|---|
| `protocol/pico.json` | Machine-readable record of every decision — the single source of truth |
| `protocol/prospero_draft.md` | Paste-ready registration, field by field, per `prompts/reference/prospero-fields.md` |
| `screening/criteria.json` | Stage 1 input, derived from `pico.json` |
| `protocol/registration.json` | Written after registering: CRD number, registration date, URL |

All paths are relative to the project root.

## The one rule that governs this stage

**Decisions are made from methodology and from the shape of the literature — never from which studies you
would like to end up with.** A scoping search tells you how many records a question returns and which
designs exist; that legitimately informs feasibility and scope. Looking at individual candidate studies and
tuning criteria to keep or drop them is criteria-fitting, and it is the thing peer reviewers check for when
they compare your registration date against your search date. If the human steers that way, say so plainly
and redirect to the methodological version of the question.

---

## Phase P-A — Sharpen the question

Take the human's question in plain language and establish, through dialogue:

1. **Review type**, because it determines everything downstream:

   | Type | Question shape | Designs usually eligible |
   |---|---|---|
   | Intervention effectiveness | Does X improve Y compared with Z? | RCTs; sometimes non-randomised studies of interventions |
   | Prevalence / burden | How common is X in population P? | Cross-sectional, cohort |
   | Prognosis | Does factor X predict outcome Y? | Prospective cohort (retrospective often excluded) |
   | Diagnostic accuracy | How well does test X detect condition Y? | Cross-sectional accuracy studies with a reference standard |
   | Aetiology / risk | Does exposure X cause outcome Y? | Cohort, case-control |

2. **Whether it is answerable as posed** — too broad ("does exercise help health"), too narrow to pool, or
   already covered by a recent review.
3. **Whether meta-analysis is plausibly in scope**, or whether this is a narrative synthesis.

Confirm the sharpened question with the human before continuing. Record the review type — later phases
branch on it.

---

## Phase P-B — The eligibility decision checklist

This is the core of the stage. Walk the checklist **item by item** and get an explicit answer to each. Do
not accept silence: an unanswered item here is a future PROSPERO amendment, and amendments are exactly what
this stage exists to prevent.

Offer a defensible default for each item and let the human accept or override — that is faster than an open
question and still forces the decision into the open. State the consequence of each choice in one line.

### Population — PROSPERO `Population — Included` / `Excluded`
- Condition and diagnostic criteria required (which guideline/definition?)
- Age bounds — exact, not "adults"
- Severity or disease-stage bounds
- Setting: inpatient / outpatient / community / ICU
- Comorbidity or co-treatment exclusions
- Mixed populations: eligible only if the subgroup is reported separately?

### Intervention — PROSPERO `Intervention(s) or exposure(s) — Included` / `Excluded`
- Exactly what counts as the intervention; which variants are in
- Dose, duration, route, intensity thresholds
- Co-interventions permitted, and must they be balanced across arms?
- Is the intervention eligible as part of a multi-component programme, or standalone only?

### Comparator — PROSPERO `Comparator(s) or control(s) — Included` / `Excluded`
- Is a comparator required at all? (No, for prevalence and single-arm questions.)
- Which comparators count: placebo, usual care, active control, another dose, waitlist?
- Head-to-head-only studies with no standard arm: in or out?
- Note PROSPERO also attaches PICO ontology tags here (e.g. "Placebo", "Usual Care").

### Study design — PROSPERO `Study design` pick-list + `Included` / `Excluded`
This is where the decisions people forget actually live. The PROSPERO dropdown is coarse (randomised or
not); all precision goes in the free-text boxes.

- Randomised only, or non-randomised designs too?
- **Prospective only, or are retrospective designs eligible?** — decide it here, explicitly
- Cluster and crossover trials: eligible? (They need special meta-analytic handling — flag if in.)
- Single-arm / before-after studies
- Case reports, case series, and the minimum n at which a series becomes eligible
- Conference abstracts, preprints, theses, trial-registry entries with results
- Secondary publications of an already-included trial
- **Minimum follow-up duration**
- **Minimum sample size**, if any

### Context, limits and publication — PROSPERO `Context`, `Study design — Included`, search fields
- Geography, health system, care setting
- **Language restrictions** — and note that restricting language is a known bias source; if the human wants
  English-only, record the justification
- **Date range**, and the reason for the lower bound (a guideline change? a technology's introduction?)
- Published-only, or grey literature and unpublished data too?

### Outcomes — PROSPERO `Main outcomes` / `Additional outcomes`
Handle this with more care than the rest: outcomes registered here bind Stage 2's extraction schema, and a
mismatch between registered and reported outcomes is selective outcome reporting — the bias reviewers hunt
hardest.

- Primary outcome(s): definition, measurement instrument, unit, **timepoint**
- Secondary outcomes, each with the same specificity
- Harms and adverse events — a review that registers no safety outcome should do so deliberately
- Whether a study is eligible if it reports none of the primary outcomes
- Which analysis population governs (ITT by default)

At the end of this phase, play the full decision set back to the human as a compact summary and get
confirmation before spending a search on it.

---

## Phase P-C — Scoping search

Purpose: check that the question is feasible and that the criteria are the right shape. Deliberately not a
screening exercise.

1. **Draft search strings** per database the review will use — at minimum the concept blocks for
   population, intervention, and design, with the controlled vocabulary each database uses (MeSH for
   PubMed/MEDLINE, Emtree for Embase).
2. **Run what you can reach.** If the harness offers literature search tools, run the population and
   intervention blocks and report **result volumes**, not candidate study lists. If it has no search access,
   hand the strings to the human to run and report counts back.
3. **Report to the human as numbers and shapes:**
   - Approximate yield of the unrestricted question
   - How much each restriction changes it (design limit, date limit, language limit)
   - Whether the relevant designs appear to exist at all — a question with no RCTs is a question that needs
     its design criteria revisited, or a different review type
   - Whether a recent review already covers this (PROSPERO's own register and the literature) — this also
     answers the registration's `Check for similar records already in PROSPERO` field
4. **Feed it back into Phase P-B.** Revisions here are legitimate and expected: they are driven by feasibility
   and by the shape of the evidence base, not by which studies would survive.

If the yield is unmanageable (tens of thousands) or near-empty, say so and work through narrowing or
broadening with the human before proceeding.

---

## Phase P-D — Methods decisions

The remaining registration fields. Same approach: propose a defensible default, force an explicit answer.

- **Databases** — main sources plus specialist/regional ones (PROSPERO `Main sources` is a pick-list from
  its own database list; regional databases go in the free-text `Other important or specialist databases`)
- **Other search methods** — reference-list checking, citation searching, contacting authors, trial registries
- **Selection process** — PROSPERO's option reads "at least two people (or person/machine combination) with
  a process to resolve differences". This harness's dual-pass screening with conflict adjudication fits that
  option; if the review uses it, declare it here rather than leaving the AI's role undeclared
- **Data extraction process** — independence, and whether authors will be contacted for missing data
- **Risk of bias tool** — matched to design: RoB 2 (RCTs), ROBINS-I (non-randomised interventions),
  QUADAS-2 (diagnostic accuracy), QUIPS (prognosis), Newcastle-Ottawa (observational)
- **Reporting bias assessment** — assessed or not
- **Certainty assessment** — GRADE domains and how the Summary of Findings tables are produced
- **Synthesis strategy** — fixed vs random effects and why; effect measures per outcome type (MD/SMD for
  continuous, RR/OR/HR for dichotomous and time-to-event); heterogeneity (I², Q); pre-specified subgroup and
  sensitivity analyses; publication-bias assessment with its ≥10-study threshold; software; narrative
  fallback when pooling is not possible
- **Review team** — each member's name, ORCID, organisation, country, conflicts; exactly one **guarantor**;
  one named contact with email
- **Funding source, affiliation, peer review status**
- **Review timeline** — start and end dates

Pre-specifying subgroup analyses matters as much as pre-specifying outcomes: subgroups invented after
seeing the data are the classic route to a spurious finding.

---

## Phase P-E — Emit the artifacts

Generate all three from the same decision set so they cannot drift apart.

1. **`protocol/pico.json`** — canonical:

```json
{
  "review_title": "...",
  "review_type": "intervention_effectiveness | prevalence | prognosis | diagnostic_accuracy | aetiology",
  "question": "the sharpened question",
  "rationale": "...",
  "objectives": "...",
  "pico": {
    "population":   {"included": "...", "excluded": "..."},
    "intervention": {"included": "...", "excluded": "..."},
    "comparator":   {"included": "...", "excluded": "...", "required": true, "pico_tags": ["Placebo"]},
    "outcomes": {
      "primary":   [{"name": "...", "definition": "...", "instrument": "...", "unit": "...", "timepoint": "..."}],
      "secondary": [{"name": "...", "definition": "...", "instrument": "...", "unit": "...", "timepoint": "..."}]
    }
  },
  "study_design": {
    "randomised_only": true,
    "prospective_only": false,
    "included": "...",
    "excluded": "...",
    "cluster_or_crossover_eligible": false,
    "min_followup": "...",
    "min_sample_size": null
  },
  "limits": {"languages": "...", "date_range": "...", "publication_status": "...", "context": "..."},
  "analysis_population_default": "ITT",
  "methods": {
    "databases": ["..."], "specialist_databases": ["..."], "other_search_methods": ["..."],
    "selection_process": "...", "extraction_process": "...",
    "rob_tool": "...", "reporting_bias": "...", "certainty": "GRADE",
    "synthesis": "...", "subgroups": ["..."], "sensitivity": ["..."]
  },
  "team": [{"name": "...", "orcid": "...", "organisation": "...", "country": "...", "guarantor": false, "coi": "none"}],
  "timeline": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "scoping_search": {"date": "YYYY-MM-DD", "strings": {"pubmed": "..."}, "yields": {"pubmed": 0}}
}
```

2. **`protocol/prospero_draft.md`** — the paste-ready registration. Follow
   `prompts/reference/prospero-fields.md` exactly: its 13 sections, in its order, with its field labels.

   **Mark every field by kind, because they are not all pasteable:**
   - **free** → give the text to paste verbatim, in a fenced block
   - **pick** → give the option to *select*, quoted exactly as PROSPERO words it. Never render a dropdown
     option as prose to paste; the human cannot paste a sentence into a dropdown
   - **struct** → give the per-entry values (team members, databases, MeSH terms, the stage matrix)
   - **auto** → state that PROSPERO fills it, so its absence is not mistaken for an omission

   Flag any field you could not fill as `⚠ NEEDS INPUT` with the specific question, rather than inventing
   content. A confident hallucination in a registration is worse than a visible gap.

   Fill **`Stage of the review at this submission`** from what has actually happened — Started/Completed
   across Pilot work, Formal searching, Screening, Data extraction, Risk of bias, Data synthesis. If only
   the scoping search has run, that is Pilot work started and nothing else. Never tick optimistically: this
   matrix is the register's own record of how prospective the registration really is.

3. **`screening/criteria.json`** — derived from `pico.json`, in the shape Stage 1 consumes: review title,
   PICO, `include_criteria`, and coded `exclude_criteria` ordered by how decisively each can be judged from
   an abstract (design and population first, outcomes last). Every `Excluded` decision from Phase P-B should
   map to a reason code; codes feed the PRISMA flow diagram.

Present all three to the human. `prospero_draft.md` is the one they will act on — walk them through the
`⚠ NEEDS INPUT` items first.

---

## Phase P-F — Register

1. The human registers at PROSPERO (login required; registration is free). They paste the free-text fields,
   select the pick-list options as marked, and fill the structured entries.
2. PROSPERO runs automated and editorial checks, and **all listed record authors must approve** the content
   before it publishes.
3. Once it has a CRD number, record `protocol/registration.json`:

```json
{"registry": "PROSPERO", "id": "CRD42026XXXXXXX", "registered_date": "YYYY-MM-DD",
 "url": "https://www.crd.york.ac.uk/PROSPERO/view/CRD42026XXXXXXX",
 "criteria_source": "protocol/pico.json"}
```

Stage 1 reads this file and records which registration it screened under. If it is absent, Stage 1 warns
that screening is proceeding unregistered — that is the human's call to make knowingly, and the review-stage
matrix on any later registration must reflect that screening had already started.

**Amendments.** If something genuinely must change after registration, edit the PROSPERO record (which
creates a new version — that is the amendment trail), update `pico.json`, and record what changed and why in
`protocol/amendments/NNN.json`. PRISMA 2020 item 24c asks you to report protocol deviations, so keep the
reason, not just the change.

---

## Rules

- Never write a registration draft the human has not confirmed decision by decision.
- Never fill a field with plausible-sounding invention; mark it `⚠ NEEDS INPUT`.
- Never tune criteria to change which studies survive; revise them for methodological precision and
  feasibility only, and say so when the distinction is at stake.
- Never tick the review-stage matrix for work that has not happened.
- Registration is prospective — before screening. If screening has already started, register anyway and
  record it truthfully.
- PROSPERO covers reviews with **health-related outcomes**. Out-of-scope reviews belong elsewhere
  (INPLASY, PROCEED, OSF) — say so rather than producing a draft that will be rejected.
- `prompts/reference/prospero-fields.md` is the field authority. If PROSPERO changes its form, update that
  reference first, then this file.
