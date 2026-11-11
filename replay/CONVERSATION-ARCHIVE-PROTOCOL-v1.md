# AX309-RDSP-001 | Conversation archive control procedure v1.0

STATUS: REQUIRED OPERATIONAL CONTROL, NOT AN AUTOMATIC CHATGPT CAPTURE INTEGRATION.

For each future engineer instruction that entails a repository operation:
1. Check git state, and read back replay/conversations.jsonl and replay/events.jsonl BEFORE changes.
2. Capture exact currently visible user message in a separate source record with role=user, completeness=FULL, source=current_chat_visible, actual historical timestamp only if known, and a project-event reference.
3. Archive complete assistant final response verbatim when available (role=assistant, completeness=FULL), before announcing logging verified. If inaccessible, log an explicit SUMMARY with provenance rather than falsely claiming FULL. Tool/status commentary can be noted separately; they are not automatically ingested.
4. Use append_conversation_v1.py with a JSON batch containing role, completeness FULL/EXCERPT/SUMMARY, source_type, source_id and event refs. The tool append-only writes with fsync, checks byte-prefix preservation, deduplicates by stable UUIDv5 source ID and full-body SHA and immediately re-reads all records.
5. Run verify_conversations_v1.py to validate unique refs, role/completeness claims, content hashes and event links. Check new records' counts and sha and create a separate coverage/gap report.
6. Commit audit evidence and report with source SHA and project Replay link. Do not delete or rewrite the 30 inherited historical excerpt records.
7. If new user/assistant text or message origin cannot be captured, declare an explicit GAP in the report and do NOT claim automatic completeness.

**Limit:** These scripts cannot intercept new ChatGPT turns autonomously. They must be invoked on each project turn while automatic capture is unavailable. Do not confuse a project event summary with verbatim assistant chat. No fabricated historical timestamp; recorded_at_utc is time of archive insertion, historical_time_utc remains null when missing.

All stage gates and S04 numeric-contract approvals remain independent of archive completeness; logging is necessary operational traceability but not evidence of numerical performance.
