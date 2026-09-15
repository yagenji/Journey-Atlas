# Data and compatibility cleanup

Updated: 2026-09-16
Closure base: `3ce1ccef23450f217130788f749bdf2e387eb629` (`main`, PR #822).
Original cleanup base: PR #810.

This document is a maintenance handoff, not Country content, visual approval, or
publication authority.

## Status

The JOURNEY ATLAS source/data/compatibility cleanup is complete subject only to the
required checks and merge/deploy verification of the closure PR carrying this file.
Remote branch deletion is intentionally separated into a later Branch Hygiene phase;
it is not required to close this data cleanup.

The cleanup did not change the established Country design contract, approved visual
assets, Map language, Theme assignments, or user approval requirements. Canonical
Country branches remain retained production history unless a later explicit Branch
Hygiene policy decides otherwise.

## Canonical scope after cleanup

- `data/atlas-destinations.json` is the single destination registry.
- Formal scope: 201 destinations.
- Asia: 49 destinations.
- Hong Kong and Macao are independent formal destinations in that registry.
- `data/atlas-destinations-editorial.json` is retired.
- `data/atlas-scope.json` is retired.
- The obsolete static production-verification target is retired.
- Theme assignment remains sourced from `data/theme-taxonomy.json`.
- Publication state remains governed by the current Country Production State /
  Publication Pipeline v2 contracts.

## Completed cleanup PRs

| PR | Result |
| --- | --- |
| #806 | Production/start documentation aligned with Content QA v6 and Publication Pipeline v2 |
| #807 | Orphaned byte-identical Bahrain Map v2 removed; referenced v3 retained |
| #808 | Obsolete static production-verification target removed |
| #809 | Conflict-sync workflow restricted to the legacy publication path |
| #810 | Editorial compatibility registry retired; canonical 201 registry established as the only registry |
| #811 | 17 unreferenced published-Country production plans removed; documentation/branch-hygiene cleanup |
| #812 | Unused top-level `theme-icons.svg` removed; stale PRs #610/#714/#715 closed |
| #813 | Stale icon, typography, and State-recovery maintenance rebuilt on current main and merged after full QA |
| #814 | Cleanup handoff synchronized after #813 |
| #815 | Obsolete 2026-09-03 published-Country renewal baseline removed |
| #816 | Duplicate `data/atlas-scope.json` retired and consumers consolidated onto canonical registry |
| #817 | Handoff synchronized after #816 and deployment verified |
| #818 | Publish/review/tmp branch audit recorded |
| #819 | Common ops branch audit recorded |
| #820 | First Country production-verification ops audit batch recorded |
| #821 | All 34 surviving `ops/*` refs classified: 33 content-preservation-safe, 1 retained |
| #822 | Noncanonical Country-slug branch audit recorded; five aliases safe and Myanmar history retained |

Historical detail for each batch remains available in the corresponding merged PR
and prior revisions of this file. Do not recreate duplicate archive documents.

## Final lifecycle branch audit

The remaining Country lifecycle families were audited individually rather than by
branch-name pattern.

### Deletion-safe from a content-preservation perspective

The following refs have no required unpreserved source content. They may be handled
in a later Branch Hygiene phase after confirming they are not open-PR heads.

- Hong Kong lifecycle family — all seven refs are preserved by merged PRs and each
  branch-head tree matches its corresponding squash-merge tree:
  - `country/hong-kong`
  - `country/hong-kong-review-state`
  - `country/hong-kong-map-fix`
  - `country/hong-kong-map-review-state`
  - `country/hong-kong-encounters-fix`
  - `country/hong-kong-encounters-review-state`
  - `country/hong-kong-publish`
- Indonesia lifecycle family — all five refs are preserved by merged PRs and each
  branch-head tree matches its corresponding squash-merge tree:
  - `country/indonesia`
  - `country/indonesia-review-verification`
  - `country/indonesia-review-state`
  - `country/indonesia-review-state-refresh`
  - `country/indonesia-publish`
- Japan:
  - `country/japan` — merged review package tree preserved
  - `country/japan-publish-final` — merged final-QA tree preserved
  - `country/japan-publish-live` — merged publication tree preserved
- `country/pakistan-repair-temp` — its head is an ancestor of canonical
  `country/pakistan`; branch-unique history is zero relative to that canonical branch.
- `country/taiwan-publish` — merged PR #641; branch-head and squash-merge tree SHAs
  are identical.

Previously audited deletion-safe groups remain valid, including:

- five noncanonical aliases: `country/kyrgyzstan`, `country/saudi-arabia`,
  `country/sri-lanka`, `country/turkey`, `country/united-arab-emirates`;
- duplicated Iraq `country/iraq-temp*` refs;
- audited Cambodia `publish/*` and `review/*` refs;
- audited China/North Korea/Russia publication refs;
- six audited top-level `tmp*` refs;
- 33 of the 34 surviving `ops/*` refs classified in #821;
- merged cleanup work branches already proven contained by main or equivalent trees.

## Redundant refs retained for intermediate history

These refs are not active sources of truth, but unique commit identities are not
fully reachable from current `main` because much of the repository uses squash
merge. They remain intentionally retained until a separate archive-tag or canonical
branch retention decision is made.

| Ref | Reason for retention |
| --- | --- |
| `country/iran-fix-tmp`, `tmp2`, `tmp3`, `tmp4` | Same intermediate head; content continues into canonical `country/iran`, but intermediate commit identities are unique |
| `country/bangladesh-sync-temp` | Intermediate history continues into canonical `country/bangladesh` but is not directly reachable from main |
| `country/philippines-sync-backup`, `country/philippines-sync-backup-2` | Same intermediate head; content continues into canonical `country/philippines` |
| `backup/iraq-pre-policy5-sync` | Intermediate history continues into canonical `country/iraq` |
| `country/myanmar` | Unique commit uploaded 13 images under the obsolete path; all 13 blobs are byte-identical to canonical `myanmarburma` assets, but the commit identity remains unique |
| `ops/tajikistan-production-qa` | Only surviving `ops/*` ref with divergent branch-unique history not fully contained by the later live-production branch |
| `country/japan-publish` | Closed unmerged PR #682 contains semantic Japan final-QA work plus a Cambodia change; do not classify as a no-op deletion |
| `country/bahrain-renewal` | Divergent branch with four semantic commits affecting Bahrain Map/data/Production State history; no direct merged PR ownership found |
| `country/singapore-clean` | Divergent four-commit temporary recovery sequence; unique files include two Singapore Production State snapshots, so preserve as intermediate provenance rather than bulk-delete |

Canonical `country/{slug}` working branches are not cleanup targets in this phase.
Their retention is a repository-history policy question, not a source/data cleanup
requirement.

## Retained dependencies

- Antarctica production material: unpublished working material; retain.
- Romania legacy production path: State remains REVIEW / final approval PENDING;
  do not migrate, publish, or remove as cleanup.
- Russia plan/provenance: retain while current State/Render Packet provenance refers
  to it.
- Legacy State/ledger helpers still imported by active validators: retain.
- `docs/REQUIRED_PR_GATES.md`: retain; its active gate/ruleset semantics still match
  repository enforcement.
- Content QA v2-v5 and Image Policy Revision 7 / 7.1 compatibility documents:
  retain while current workflows/authority documents reference them.
- Older general design/workflow documentation is not removed merely for age; change
  it only when an active authority/reference conflict is demonstrated.

## Final source scan

The final cleanup scan on current main found:

- no surviving source reference to `data/atlas-destinations-editorial.json`;
- no surviving source reference to the retired static production-verification target;
- `data/atlas-scope.json` appears only in this cleanup history/documentation context,
  not as an active consumer dependency;
- the top-page destination count is 201;
- no open pull request existed before opening the closure PR for this handoff.

## Closure and next phase

Once the closure PR containing this revision passes the required Publication Pipeline
v2 / Browser QA checks, merges to `main`, and its Cloudflare Pages deployment succeeds,
the data/compatibility cleanup is closed.

Any later deletion of refs classified above belongs to **Branch Hygiene Phase 2**.
That phase must continue to protect `main`, `review-previews`, open-PR heads, active
Country branches, and any retained unique-history refs. Branch deletion is not a
prerequisite for declaring this cleanup complete.
