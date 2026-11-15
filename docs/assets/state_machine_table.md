| from | guard | to | meaning |
|---|---|---|---|
| INGEST | `ingest_failed` | ERROR | the file could not be opened or has no pages |
| INGEST | _(fallback)_ | CLASSIFY | ingested |
| CLASSIFY | _(fallback)_ | EXTRACT | digital or scanned, document type, template id |
| EXTRACT | `extract_empty_and_tier_left` | ESCALATE_TIER | the tier produced no rows and a more expensive tier is available |
| EXTRACT | `extract_empty` | HUMAN_REVIEW | nothing extracted, no tier left |
| EXTRACT | _(fallback)_ | GROUND | candidate reading produced |
| GROUND | _(fallback)_ | VERIFY | ungrounded values are marked, never silently kept |
| VERIFY | `accepts` | ACCEPT | all invariants pass and policy met |
| VERIFY | `repairable` | REPAIR | localized failure, repair budget left |
| VERIFY | `tier_left` | ESCALATE_TIER | failure, a better tier is available |
| VERIFY | _(fallback)_ | HUMAN_REVIEW | budget exhausted |
| REPAIR | `repair_proposed` | GROUND | candidate from the source |
| REPAIR | `tier_left` | ESCALATE_TIER | repair found nothing, tier available |
| REPAIR | _(fallback)_ | HUMAN_REVIEW | repair found nothing, no tier left |
| ESCALATE_TIER | `tier_advanced` | EXTRACT | next tier, failed region only |
| ESCALATE_TIER | _(fallback)_ | HUMAN_REVIEW | no tier left within budget |
