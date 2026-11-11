# AX309-RDSP-001 | S04 Conversation Archive Recovery v1.0

**Phase 1 verified, manual append-only recovery, no automatic capture claimed.**

## Recovery scope and counts

| Category | Rows | Accuracy claim |
|---|---:|---|
| Pre-existing legacy user excerpts (unchanged original bytes) | 30 | EXCERPT only, not full user messages |
| New FULL user messages transcribed from currently visible conversation | 5 | FULL content and SHA-256; exact original historical timestamp unknown |
| New S04 agent/project activity SUMMARIES sourced from events E106..E111 | 6 | SUMMARY, NOT verbatim assistant reply |
| New assistant FULL message in phase1 | 0 | Pending capture of this response in separate archive operation |
| **Total archive rows after phase1** | **41** | All JSONL read back, unique refs and event links validated |

Recovered FULL user instructions include engineer-approved Gate-S03 and S04 entry, numeric contract v0.2 authorization, a connection check, S04-C01 input scaling hold instruction and current input-policy/archive-recovery request. These are only the visibly available exact text selections; no unknown earlier assistant message is labeled FULL.

## Integrity checks

- Old 30-row prefix byte-for-byte preserved, prefix SHA-256 9c17d24d6264dedc5d18f3ab8c07f3ce3675e441fc190c9bd8b4caf90582cac4.
- For new rows: UTF-8 text, declared role and completeness, immutable source type/id, unique UUIDv5 message_ref, SHA-256 full text, time of archive insertion, nullable unknown original historical time, project-event references E106..E112.
- Recovery batch was rerun; 0 duplicates added. Re-read JSONL proved 41 JSON objects, 5 full-content SHA verified, 6 summaries, 30 legacy excerpts and no broken project-event links.
- The old legacy 30-row schema (verbatim_excerpt and is_full_message false) remains untouched. All new fields supplement, not rewrite, old rows.
- These six event-derived summaries are NOT evidence that six verbatim assistant messages were recovered.

## Gaps and restrictions

1. Machine archive contained no full historical assistant responses and only older user excerpts. Six historical agent summaries are explicitly nonverbatim, and some older S04 messages may be missing.
2. Original sent timestamps for manual recoveries are unavailable; recorded_at_utc is the timestamp of recovery, not fabricated chat time.
3. No automatic interception of ChatGPT message streams is available through these scripts. Every future project turn must append exact user and final assistant text if available, separately log unverifiable/summary text, then run post-append verification before reporting completion.
4. This report is a phase1 snapshot. The present agent's final user-visible response is to be logged as FULL in a follow-up append operation; it is not counted above.

## S04 policy and engineering holds

Companion decision proposal: engineering/S04-C01-INPUT-POLICY-DECISION-PACKAGE-PROPOSED-v0.4.md; exact host metadata JSON Schema v0.4 in engineering/S04-C01-input-metadata-PROPOSED-v0.4.schema.json. No g allowlist, scaling, A/B format, FFT shift schedule or error acceptance rule approved; S04-C01 and C02 OPEN, Gate-S04 OPEN, S04 0%, total 25%. Accepted Pfa/Pd seeds have not been used; no statistical main trial, RTL or hardware was run.

## File SHA-256
- replay/conversations.jsonl: 5b4fb92b26c63837cd810ad0f8e5cc0640d6808f3ef4ee7c9db9e4d13bddf3bd
- replay/append_conversation_v1.py: ea53c0629565c3dbcb89a77b7980e75b9c8f37d22e816a98a40c14c98df6393e
- replay/verify_conversations_v1.py: a34e45e9ccccb3f0e3b4c758310847f4575625f00f8c894faa0aa8ebfa7d21ae
- replay/CONVERSATION-ARCHIVE-PROTOCOL-v1.md: 35034621e3ae9d55ee16d651b950c3d56f20d45495e9b9fe03f5d791a93b9042
- engineering/S04-C01-INPUT-POLICY-DECISION-PACKAGE-PROPOSED-v0.4.md: 99875e4e31bc11ced0e71e883a84371ff9a3f603b6aa31ed6ace73d7193f6f9b
- engineering/S04-C01-input-metadata-PROPOSED-v0.4.schema.json: cef7cfe8e6fd7f472af2f7320f9583ff6d18407a10c4276571210d5ffb375c20
- engineering/S04-C01-INPUT-SCALING-NUMERIC-CONSISTENCY-REVIEW-v0.3.md: 6824f213187576b28fcadac72872e42bade88629a9d33bcb5a4218272d1d848d

Recovery report prepared UTC: 2026-11-11T09:49:37.437095+00:00
