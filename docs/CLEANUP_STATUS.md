# Data and compatibility cleanup

Updated: 2026-09-15
Audit base: `047698450a7b179b265e223fd763bcb4442dcb68` (`main`, PR #810).

This is a maintenance handoff, not Country content or publication authority.
The cleanup remains in progress. A merged cleanup PR does not establish that
all obsolete data, documentation, or compatibility paths have been retired.

## Scope and preservation rules

- Remove proven obsolete or duplicate authoring data and compatibility paths.
- Use the canonical 201-entry `data/atlas-destinations.json`, including Hong Kong
  and Macao; Asia contains 49 destinations.
- Preserve Country content, approved assets, maps, theme assignments,
  publication/approval state, and the established UI.
- Check live references before deletion. Age, filename, and publication alone
  are insufficient evidence that a file can be removed.
- Preserve deleted historical plans in Git history. Do not create duplicate
  archive files or rewrite approval provenance to make a deletion possible.

## Completed on the audit base

| PR | Completed cleanup |
| --- | --- |
| [#806](https://github.com/yagenji/Journey-Atlas/pull/806) | Protocol/start docs aligned with Content QA v6 and Publication Pipeline v2 |
| [#807](https://github.com/yagenji/Journey-Atlas/pull/807) | Orphaned, byte-identical Bahrain Map v2 removed; referenced v3 retained |
| [#808](https://github.com/yagenji/Journey-Atlas/pull/808) | Obsolete static production-verification target and references removed |
| [#809](https://github.com/yagenji/Journey-Atlas/pull/809) | Conflict-sync workflow restricted to the legacy publication path |
| [#810](https://github.com/yagenji/Journey-Atlas/pull/810) | Editorial compatibility registry retired; consumers use canonical registry; image versioning preserved |

## This follow-up change

- Remove 17 published-Country content plans that have no remaining repository
  references outside the old documentation index: Belarus, China, Hong Kong,
  Hungary, Indonesia, Japan, Macao, Moldova, Mongolia, Nepal, North Korea,
  Poland, Serbia, South Korea, Spain, Taiwan, and Tajikistan.
- Where a Country Production State exists, its phase is `COMPLETE`; all 17
  canonical registry rows are published. No open PR targets their production
  branches at the audit time.
- Update the documentation index to current authority documents and actual
  retained plans; remove the stale description of Tajikistan as unfinished.
- Remove the historical push-triggered branch deletion and its hard-coded
  target from `branch-hygiene.yml`. Explicit manual branch selection and the
  existing main-branch protection remain. This change deletes no Git branch.

## Subsequent cleanup

- Remove `assets/images/top/theme-icons.svg`. No HTML, CSS, JavaScript, JSON,
  workflow, documentation, or build input references the file. The top page
  renders its theme controls from HTML/CSS, while `scripts/package_site.py`
  otherwise copies every file under `assets/images/top/` into production.
- Close obsolete PRs #610, #714, and #715. Russia is already complete with a
  later approved FOOD03 generation, and the two old publication/QA trigger PRs
  were superseded by later full published-Country QA and Pipeline v2 cleanup.

## Retained dependencies and outstanding review

| Item | Evidence / next decision |
| --- | --- |
| Antarctica plan and QA | Unpublished draft; retain working material |
| Romania plan and legacy publication path | Main State is `REVIEW`, final approval is `PENDING`, and Render Packets reference the plan. Do not auto-migrate, publish, or remove dependencies as cleanup |
| Russia plan | Published, but main State Render Packets still reference it. Retain provenance |
| Legacy State/ledger helpers | Still imported by active validators. No removal or identifier-normalization changes in this cleanup |
| Renewal plans/audits and reference briefs | Separate renewal/reference evidence; not covered by the completed-production-plan deletion decision |
| Older general design/workflow documentation | Further authority and implementation reconciliation is needed; no design contract is changed by this follow-up |
| Open PRs #647, #651, #656 | Their unique changes are not on main. Revalidate against current icon, CSS-ownership, and State-recovery contracts before integration or closure |
| Remote branch inventory | Far above the `WORKFLOW.md` steady-state rule. Delete only after checking open PR ownership and whether unique history requires an archive tag |
| Production deployment / live QA after #810 | Separate from pre-merge Browser QA; not verified by this repository cleanup |

## Audit boundaries

- No duplicate keys were found in tracked JSON on the audit base.
- No retired editorial registry or static verification-target path references
  were found in current tracked sources on the audit base.
- An exact full-path image search is not sufficient to prove an orphan:
  `world-map-watercolor.svg` is referenced through a relative CSS URL. The
  removed `theme-icons.svg` was also checked by basename and relative-path
  searches and had no consumer. The packager's whole-directory copy made it a
  production payload despite the absence of a runtime reference.
- Repository validation proves source consistency only. It does not establish
  visual approval, production deployment success, or completion of the wider
  cleanup. Continue from the outstanding items above using the latest main.
