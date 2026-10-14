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
