# Release 0.1.0 verification

- 19 unittest cases pass on macOS / Python 3.9.
- All 31,101 packaged `code -> sentence` pairs exactly match the official offline browser export used for this release. No spelling/spacing correction was made.
- The corpus has 66 books and 1,189 chapters, no duplicate code, and no empty sentence.
- Packaged-data SHA-256 and compressed-container SHA-256 are checked at load time.
- Socket construction is blocked during the CLI lookup test; lookup succeeds without network.
- Invalid/missing references, corrupt data, empty quotation lists, modified text, unordered excerpts, and reference-only input do not falsely pass.
- Compound references preserve the stated order, including `마24:36,33`.
- A previously generated sermon Markdown was read without modification as a diagnostic example. Its quotations are not declared correct merely because an earlier structural validator passed. No sermon skill or existing sermon document was edited.
- A portable pure-Python wheel is built with the corpus included. Offline installation is tested using `pip --no-index --no-deps` in a separate environment.
- Windows syntax/usage is documented, but this release has not been executed on a Windows host.

Tests check implementation and preservation, not whether Tov's text is theologically or editorially correct. Tov is the chosen authority. No alternative Bible corpus or website is used for quotation verification.

## Public sermon-skill bundle

- The current sermon skill's instructions, templates, both unchanged Python helpers, setup guide, and upstream metadata/reference files are included under `skills/youtube-video-transcript`.
- Setup documentation now points to the public repository; cloning requires no GitHub or Tov account. Local installation paths and executable-path handoff are documented.
- Both skill folders pass the skill frontmatter validator. Bundled relative links are checked.
- 21 unittest cases cover the original CLI behavior and preserving exact Tov quotation text through Apple Notes formatting.
- No personal memory, captions, completed sermons, browser exports, cookies, or credentials are added to the public skill bundle.
- This packaging verification is not a new full YouTube-sermon run. The initial CLI-only verification above is historical; the current sermon skill has since been connected to Tov.
