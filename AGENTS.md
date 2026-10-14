# Tov Bible CLI invariants

- Runtime must remain offline and account-free. Do not add authentication, cookies, HTTP calls, analytics, or other Bible fallbacks.
- The only verse source is the packaged Tov `kor` snapshot. Preserve original `sentence` bytes; do not fix spelling from memory or another translation.
- Data changes require explicit user authorization, acquisition provenance, hashes, structural checks, reviewed diff, and a version change. Do not overwrite data automatically.
- Source links are provenance, not permission for network requests at runtime.
- Keep personal annotations/history and credentials out of the corpus and Git history.
- Match errors and pagination honestly. No quotations or reference-only verification cannot count as complete quote validation.
- Run meaningful tests and packaged-data smoke tests before release. Never claim Windows validation based only on a platform-independent wheel.
- Installation/lookup requests do not authorize editing or pushing this remote repository. Install both skill folders and the CLI without overwriting existing user skills; preserve their sermon workflow and Tov-only source rule.
