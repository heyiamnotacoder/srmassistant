# PROSPERO registration form — verified field reference

**Verified 2026-09-03** against the live register (platform release 2.0.40, the form introduced
24 February 2025) by reading four published records end to end:
CRD420261408785, CRD420251029033, CRD420261382589, CRD420251077877.

The section order and field labels below are exactly those the register renders. `prompts/protocol-builder.md`
generates `protocol/prospero_draft.md` against this file — when PROSPERO changes its form, update this
reference first, then the builder.

## How to read the field table

Every field is one of four kinds, and the generated draft must treat them differently:

| Kind | Meaning | What the draft gives the user |
|---|---|---|
| **free** | Free-text box | Text to paste verbatim |
| **pick** | Dropdown / radio / checkbox with fixed wording | The option to select, quoted exactly — never prose to paste |
| **struct** | Repeating structured entry (people, dates, tags) | Field-by-field values per entry |
| **auto** | Filled by PROSPERO itself | Nothing — noted so the user is not surprised |

A `pick` field rendered as pasteable prose is the single most common way a generated draft wastes the
user's time: they cannot paste "Only published studies will be sought" into a dropdown.

## 1. REVIEW TITLE AND BASIC DETAILS

| Field | Kind | Notes |
|---|---|---|
| Review title | free | Include design ("...: A Systematic Review and Meta-Analysis") |
| Condition or domain being studied | free + auto | Free text; PROSPERO also attaches coded condition terms |
| Rationale for the review | free | Why this review, now — including what existing reviews missed |
| Review objectives | free | Explicit objectives, distinct from the rationale |
| Keywords | free | Semicolon-separated; not shown publicly but indexed for search |
| Country | struct | One or more countries of the review team |

## 2. ELIGIBILITY CRITERIA

Each element below is **split into Included and Excluded boxes**. This split is new in the 2025 form and is
where a protocol-development stage earns its keep: an unstated exclusion here becomes an amendment later.

| Field | Kind | Notes |
|---|---|---|
| Population — Included | free | |
| Population — Excluded | free | Optional but expected; state age bounds, comorbidity, setting exclusions |
| Intervention(s) or exposure(s) — Included | free | |
| Intervention(s) or exposure(s) — Excluded | free | |
| Comparator(s) or control(s) — Included | free + struct | Free text plus PICO ontology tags (e.g. "PICO tags selected: Placebo", "Usual Care") |
| Comparator(s) or control(s) — Excluded | free | |
| Study design | **pick** | Observed: `Only randomized study types will be included.` |
| Study design — Included | free | Where prospective/retrospective, RCT-only, language and date limits are actually stated |
| Study design — Excluded | free | Observed: non-randomised, observational, qualitative, reviews, case reports, protocols, conference abstracts without full text |
| Context | free | Setting, geography, health system, culture |

> The prospective-vs-retrospective decision lives in **Study design — Included/Excluded**, not in Population.
> The `Study design` pick-list is coarse (randomised vs not); the precision goes in the free-text boxes.

## 3. TIMELINE OF THE REVIEW

| Field | Kind | Notes |
|---|---|---|
| Date of first submission to PROSPERO | auto | |
| Review timeline | struct | Review start date and end date |
| Date of registration in PROSPERO | auto | |

## 4. AVAILABILITY OF FULL PROTOCOL

| Field | Kind | Notes |
|---|---|---|
| Availability of full protocol | **pick** + free | Options observed: written and uploaded to PROSPERO (yields a PROSPEROFILES link); written but not available, **with a required reason**; not written |

## 5. SEARCHING AND SCREENING

| Field | Kind | Notes |
|---|---|---|
| Search for unpublished studies | **pick** | Observed: `Only published studies will be sought.` |
| Main sources that will be searched | **struct** | Chosen from PROSPERO's database list; renders as "The main databases to be searched are CLIB - The Cochrane Library, Embase.com." |
| Other important or specialist databases that will be searched | free | Free text — regional/specialist databases (CNKI, VIP, Wan Fang, SinoMed) go here |
| Search language restrictions | **pick** | Observed: `There are no language restrictions.` |
| Search date restrictions | **pick** | Observed: `There are no search date restrictions.` |
| Other methods of identifying studies | **pick** | Observed: `No other methods will be used.` / `Other studies will be identified by: contacting authors or experts.` |
| Link to search strategy | **pick** + free | Upload a PDF (yields a PROSPEROFILES link) or point at the full protocol |
| Selection process | **pick** | Observed: `Studies will be screened independently by at least two people (or person/machine combination) with a process to resolve differences.` |
| Other relevant information about searching and screening | free | Defaults to `None` |

> **"(or person/machine combination)"** is PROSPERO's own wording. Dual-pass AI screening is registrable
> under this option, provided a difference-resolution process is described. Say so here rather than
> leaving the AI's role undeclared.

## 6. DATA COLLECTION PROCESS

| Field | Kind | Notes |
|---|---|---|
| Data extraction from published articles and reports | **pick** ×2 | Independence statement, plus whether authors will be contacted for missing data |
| Study risk of bias or quality assessment | **pick** ×3 | Tool (e.g. `Cochrane RoB-2`), independence statement, whether investigators will be contacted |
| Reporting bias assessment | **pick** | Observed: `Risk of bias due to missing results will be assessed` / `will not be assessed` |
| Certainty assessment | free | GRADE approach, domains, how SoF tables are produced |

## 7. OUTCOMES TO BE ANALYSED

| Field | Kind | Notes |
|---|---|---|
| Main outcomes | free | Definition, measure, units, timepoints |
| Additional outcomes | free | Defaults to `There are no additional outcomes.` |

> This is the field that binds Stage 2's extraction schema. Outcomes registered here and outcomes
> extracted later must match, or the review is open to a selective-outcome-reporting challenge.

## 8. PLANNED DATA SYNTHESIS

| Field | Kind | Notes |
|---|---|---|
| Strategy for data synthesis | free | Model (fixed/random), effect measures per outcome type, heterogeneity (I², Q), subgroup and sensitivity analyses, publication-bias assessment and its ≥10-study threshold, software, narrative fallback |

## 9. CURRENT REVIEW STAGE

| Field | Kind | Notes |
|---|---|---|
| Stage of the review at this submission | **struct** | A Started/Completed checkbox matrix over six fixed stages: Pilot work; Formal searching/study identification; Screening search results against inclusion criteria; Data extraction or receipt of IPD; Risk of bias/quality assessment; Data synthesis |
| Review status | **pick** | Observed: `The review is currently planned or ongoing.` |
| Publication of review results | **pick** | Observed: `Results of the review will be published.` / `...will be published in English.` |

> The stage matrix is the register's own honesty check on prospective registration. A record ticking
> "Screening ... Started" is declaring itself partly retrospective. The builder must fill this from what
> has actually happened, never optimistically.

## 10. REVIEW AFFILIATION, FUNDING AND PEER REVIEW

| Field | Kind | Notes |
|---|---|---|
| Review team members | **struct** | Per person: title, name, ORCID, organisation, country, conflict-of-interest declaration; exactly one flagged **review guarantor** |
| Named contact | **struct** | One team member plus email |
| Review affiliation | free | |
| Funding source | **pick** + free | Observed: `Review has no funding and no agreed support from an academic institution and is done in authors' own time.` |
| Peer review | **pick** | Observed: `There has been no peer review of this planned review.` |

## 11. ADDITIONAL INFORMATION

| Field | Kind | Notes |
|---|---|---|
| Additional information | free | Optional — reporting guideline adherence, documentation practice, how amendments will be recorded |
| Review conflict of interest | **pick** + free | Review-level, separate from the per-member declarations |
| Medical Subject Headings | **struct** | MeSH terms; the register has a MeSH picker |

## 12. SIMILAR REVIEWS

| Field | Kind | Notes |
|---|---|---|
| Check for similar records already in PROSPERO | free | You must search the register for overlapping reviews and say what you found, or why you did not check |

## 13. Record footer (auto)

Version history (`Version 1.0, published <date>`) and PROSPERO's standard disclaimer. Nothing to supply.
Later edits create new versions — this is the amendment trail.

## Constraints the builder must respect

- **Registration is prospective.** Register before screening starts. The stage matrix records the truth
  either way, so an honest record beats a flattering one.
- **You must be logged in to register**, and registration is free.
- **All listed record authors must approve** the content before publication, following automated and
  editorial checks.
- **Character limits were not observable** from published records. Do not assert limits in generated
  guidance; keep free-text answers tight regardless.
- **PROSPERO covers reviews with health-related outcomes.** A review outside that scope belongs elsewhere
  (INPLASY, PROCEED, OSF).
