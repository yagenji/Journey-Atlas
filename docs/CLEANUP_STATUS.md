# Data and compatibility cleanup

Updated: 2026-09-16
Current continuation base: `5f6355f12d480acae25710906c5f8336aab904da` (`main`, PR #818).
Original cleanup base: PR #810.

This is a maintenance handoff, not Country content or publication authority.
The cleanup remains in progress. A merged cleanup PR does not establish that
all obsolete data, documentation, compatibility paths, or stale branches have
been retired.

## Scope and preservation rules

- Remove proven obsolete or duplicate authoring data and compatibility paths.
- Use the canonical 201-entry `data/atlas-destinations.json`, including Hong Kong
  and Macao; Asia contains 49 destinations.
- Preserve Country content, approved assets, maps, theme assignments,
  publication/approval state, and the established UI.
- Check live references before deletion. Age, filename, and publication alone
  are insufficient evidence that a file or branch can be removed.
- Preserve deleted historical plans and audits in Git history. Do not create
  duplicate archive files or rewrite approval provenance to make a deletion possible.
- Do not delete a branch only because its name contains `tmp`, `temp`, `backup`,
  `review`, or `publish`; confirm main containment or an equivalent merged tree.

## Completed cleanup

| PR | Completed cleanup |
| --- | --- |
| [#806](https://github.com/yagenji/Journey-Atlas/pull/806) | Protocol/start docs aligned with Content QA v6 and Publication Pipeline v2 |
| [#807](https://github.com/yagenji/Journey-Atlas/pull/807) | Orphaned, byte-identical Bahrain Map v2 removed; referenced v3 retained |
| [#808](https://github.com/yagenji/Journey-Atlas/pull/808) | Obsolete static production-verification target and references removed |
| [#809](https://github.com/yagenji/Journey-Atlas/pull/809) | Conflict-sync workflow restricted to the legacy publication path |
| [#810](https://github.com/yagenji/Journey-Atlas/pull/810) | Editorial compatibility registry retired; consumers use canonical registry; image versioning preserved |
| #811 | 17 unreferenced published-Country content plans removed; documentation index and branch-hygiene behavior cleaned up |
| #812 | Unused top `theme-icons.svg` removed and obsolete PRs #610, #714, #715 closed |
| [#813](https://github.com/yagenji/Journey-Atlas/pull/813) | Stale icon, typography, and State-recovery maintenance reconstructed on latest main and merged after current validation and full Browser QA |
| [#814](https://github.com/yagenji/Journey-Atlas/pull/814) | Cleanup handoff synchronized with the completed #813 reconciliation and branch-audit rules |
| [#815](https://github.com/yagenji/Journey-Atlas/pull/815) | Obsolete 2026-09-03 published-Country renewal baseline removed after confirming no surviving repository references; current renewal authority retained |
| [#816](https://github.com/yagenji/Journey-Atlas/pull/816) | Duplicate `data/atlas-scope.json` retired; destination scope, registry, and publication state consolidated onto canonical `data/atlas-destinations.json` |
| [#817](https://github.com/yagenji/Journey-Atlas/pull/817) | Cleanup handoff synchronized after #816 and deployed successfully from `main` |
| [#818](https://github.com/yagenji/Journey-Atlas/pull/818) | Remote publish/review/tmp branch audit recorded; deletion-safe refs separated from redundant refs whose squash-merge-era intermediate history remains retained |

## Current follow-up

- Continue the remote branch inventory using open-PR ownership plus main
  containment/equivalent-tree evidence; do not bulk-delete by naming pattern.
- Continue the remaining Country-specific `ops/*` production-verification audit.
  Most have merged operational PR provenance, but each ref still needs main
  containment or equivalent-tree evidence before unconditional deletion-safe status.
- For old sync/backup branches whose commits are ancestors of merged Country
  branches, preserve the intermediate history until an archive-tag or canonical
  Country-branch retention decision makes deletion provenance explicit.
- Reconcile older general design/workflow documentation only after confirming
  current authority and active implementation references. Do not change the design
  contract as part of cleanup.
- Keep `docs/REQUIRED_PR_GATES.md`: although it is not listed in the documentation
  index, its `validate` / `browser-qa`, squash-only, deletion, non-fast-forward,
  and review-thread rules match the active `Protect main` repository ruleset.
- Keep Content QA v2-v5 and Image Policy Revision 7 / 7.1 compatibility documents.
  Active workflows and current authority documents still reference those versions.

## #813 reconciliation complete

- #813 merged to `main` as `c6744bd94d69c5f011dc8bb63e69502cb302976a`.
- Before merge, the current head passed Country data validation, Publication
  Pipeline v2 checks, Production State routing, the Country icon integrity audit,
  all unpublished reviewable Country Browser QA, and all published Country
  Browser QA.
- #647 was superseded by the current icon-integrity audit and shared sprite fixes.
  Stale fixed Travel Scale / `transport.icon=road` constraints were intentionally
  not restored because they are not part of the current Country contract.
- #651 was superseded by the current Transport typography ownership fix without
  changing rendered typography values.
- #656 was superseded by `STATE_RECOVERY_MIGRATION.md` rewritten for Image Policy
  7.2 / Protocol 2. Recovery metadata remains audit provenance, not a validator
  bypass or raster-materialization path.
- #647, #651, and #656 were each annotated as superseded and closed without merge.
- No Country images, Maps, Theme assignments, Country page structure, or
  publication state were changed by #813.

## #815 obsolete renewal baseline retired

- #815 merged to `main` as `1901d4a2b5fbbc8ea6f073334da5bdabf8ff61af`.
- `docs/PUBLISHED_COUNTRY_AUDIT_20260903.md` was removed after repository search
  confirmed that no surviving source referenced it outside the obsolete audit itself.
- The removed file was a one-time automated baseline from the start of the then-28-country
  renewal program, not current publication or renewal authority.
- Current renewal status remains `data/country-renewal-status.json`; historical audit
  content remains available in Git history.
- `docs/REQUIRED_PR_GATES.md`, Content QA v2-v5, and Image Policy Revision 7 / 7.1
  were explicitly retained because they still match or are referenced by active contracts/workflows.
- No Country JSON, images, Maps, Themes, UI, or publication state changed in #815.

## #816 duplicate destination scope retired

- #816 merged to `main` as `8cbd3b7561f303694a841522601b62a0d01b1bfb`.
- `data/atlas-scope.json` was removed after its remaining repository consumers were
  migrated to the canonical 201-entry `data/atlas-destinations.json` registry.
- `scripts/validate_destination_scope.py` now validates count, ordering, special
  destinations, region membership, Hong Kong/Macao route-publication contracts,
  and Asia=49 directly from the canonical registry plus `region-taxonomy.json`.
- The editorial-neutrality note for Taiwan, Hong Kong, Macao, and Antarctica was
  preserved in documentation rather than duplicated as a second data registry.
- No Country content, approved assets, Maps, Themes, UI, or publication state changed.

## Branch cleanup audit

Branch cleanup is still in progress. No branch should be removed until its open
PR ownership and unique-history status have been checked.

### Deletion-safe from a content-preservation perspective

- All `cleanup/*` work branches through #818 have main containment or an equivalent
  merged tree. The cleanup connector still cannot delete branches.
- `cleanup/remove-completed-renewal-docs` is an ancestor of current `main` with no
  branch-unique commits.
- Cambodia's obsolete `publish/cambodia-20260911` branch is superseded by merged
  PR #688; PR #687 and #688 carry the same three-file publication diff.
- `publish/china-20260910`, `publish/northkorea-20260911-v2`, and
  `publish/russia-20260910` are preserved by merged PRs #637, #662, and #622;
  each branch head and its squash-merge commit have identical tree SHAs.
- All eight audited Cambodia `review/*` branches are either ancestors of `main` or
  have branch-head trees preserved by their merged PRs (#676, #678, #679, #681,
  #684, #685, #686).
- `tmp-delete-me-singapore`, `tmp-delete-me-singapore-2`, `tmp-do-not-use`,
  `tmp-noop`, `tmp-noop2`, and `tmp-sync-not-needed` are all ancestors of `main`
  with no branch-unique history.
- The duplicated Iraq `country/iraq-temp*` set was previously audited as safe and
  remains a deletion-safe candidate.
- `ops/country-production-protocol-2` is preserved by merged PR #692; branch-head
  and squash-merge trees are identical.
- `ops/full-published-country-qa-20260913` is preserved by merged PR #744;
  branch-head and squash-merge trees are identical.
- `ops/image-round-throughput-fix`, `ops/image-policy-revision-7`, and
  `ops/image-policy-7-1-throughput` are preserved by merged PRs #642, #643,
  and #644 respectively; each branch-head tree matches its squash-merge tree.
- `ops/brunei-production-verification` has no direct PR ownership, but its head
  is an ancestor of current `main` with zero branch-unique commits.

### Redundant refs whose intermediate history is still retained

The following branches are not active sources of truth. Their heads are ancestors
of the corresponding canonical Country branches, and those Country branches were
subsequently merged through the listed PRs. However, because the repository uses
squash merge, the intermediate commit identities are not necessarily reachable
from `main`. Keep these refs until an archive-tag or explicit canonical-branch
retention decision closes that history-preservation question.

| Redundant branch/ref | Preservation evidence |
| --- | --- |
| `country/iran-fix-tmp`, `tmp2`, `tmp3`, `tmp4` | All four refs point to `c85249fcdf564288d3687cea3a1573a4da4c0112`; that head is an ancestor of `country/iran`, which merged in PR #750 |
| `country/bangladesh-sync-temp` | Head `1595a936a859e030a595cdc37ace3ea7f57beacf` is an ancestor of `country/bangladesh`, which merged in PR #723 |
| `country/philippines-sync-backup`, `country/philippines-sync-backup-2` | Both refs point to `0036174f03450b539de752e8d8703f796cd90d23`; that head is an ancestor of `country/philippines`, which merged in PR #697 |
| `backup/iraq-pre-policy5-sync` | Head `bedb7612a0bd876b8e7bb454afa1b16079492b1d` is an ancestor of `country/iraq`, which merged in PR #781 |

These refs are therefore proven redundant as working branches, but are not yet
classified as unconditional deletion-safe archival history.

### Ops refs retained pending stronger provenance

- `ops/tajikistan-production-qa` is not an ancestor of `main`. It retains branch-
  unique commits, and comparison with the later merged
  `ops/tajikistan-live-production-qa` branch still shows divergent history rather
  than full containment. Keep it until its unique commits are classified as
  obsolete/equivalent or archived explicitly.
- The remaining Country-specific `ops/*` production-verification refs have mostly
  been mapped to merged operational PRs, but are not yet marked deletion-safe in
  bulk. Verify branch-head containment or equivalent squash-merge trees first.

The current GitHub connector does not expose branch deletion, so branches judged
safe have not been deleted through this cleanup session.

## Retained dependencies and outstanding review

| Item | Evidence / next decision |
| --- | --- |
| Antarctica plan and QA | Unpublished draft; retain working material |
| Romania plan and legacy publication path | Main State is `REVIEW`, final approval is `PENDING`, and Render Packets reference the plan. Do not auto-migrate, publish, or remove dependencies as cleanup |
| Russia plan | Published, but main State Render Packets still reference it. Retain provenance |
| Legacy State/ledger helpers | Still imported by active validators. No removal or identifier-normalization changes in this cleanup |
| Renewal plans/audits and reference briefs | Separate renewal/reference evidence; remove only an audit proven obsolete and unreferenced |
| Older general design/workflow documentation | Further authority and implementation reconciliation is needed; no design contract is changed by this cleanup |
| Remote branch inventory | Continue auditing remaining Country production-verification and other `ops/*` branches; do not bulk-delete by naming pattern |
| Intermediate sync/backup history | Decide archive-tag or canonical Country-branch retention policy before deleting refs whose commits are not directly reachable from `main` after squash merge |
| Tajikistan legacy ops history | `ops/tajikistan-production-qa` remains divergent and is retained pending explicit provenance classification |
| Production deployment / live QA after cleanup | Separate from pre-merge Browser QA; repository validation alone does not establish live production correctness |

## Audit boundaries

- No duplicate keys were found in tracked JSON on the original cleanup audit base.
- No retired editorial registry or static verification-target path references
  were found in current tracked sources on that audit base.
- An exact full-path image search is not sufficient to prove an orphan:
  `world-map-watercolor.svg` is referenced through a relative CSS URL. The
  removed `theme-icons.svg` was also checked by basename and relative-path
  searches and had no consumer. The packager's whole-directory copy made it a
  production payload despite the absence of a runtime reference.
- Repository validation proves source consistency only. It does not establish
  visual approval, production deployment success, or completion of the wider
  cleanup. Continue from the outstanding items above using the latest `main`.
