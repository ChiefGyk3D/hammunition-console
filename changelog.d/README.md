One file per change: `changelog.d/<pr-or-branch>.<kind>.md`, kind one of `added`, `changed`, `fixed`,
`removed`, `docs`, `decision`, holding one entry that starts with its `- ` bullet. Never edit
`CHANGELOG.md` in a pull request; `python3 scripts/changelog.py assemble --version vX.Y.Z --date YYYY-MM-DD`
writes the release section and deletes the fragments.
