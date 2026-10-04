<!--
SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Changelog

One entry per release, assembled from the fragments each merged pull request adds under
`changelog.d/` (never edited here in a pull request).

## Unreleased

Nothing yet.

## v0.1.0 — 2026-10-04

- **The first release.** A full-screen terminal front end for the Hammunition engine: Home (health, station, last run, units behind their pin, a first-run checklist), Install (profiles and units, the engine's plan, then the real command in a terminal pane where a person types any consent), Station, Logs, Update and Help. It reads only `hammunition <verb> --json`, never passes the engine's assume-yes flag, never sets a scripted-consent variable, and stores only its own config. Needs `python3-urwid` 2.6 or later and the engine 0.20.0 or later; the engine's per-profile installed state and its `update` report for retired units are used when present and shown as unknown when not.

- `install.sh` and `uninstall.sh` put the console under a prefix (`--prefix`, `--interpreter`) with its man page; the release workflow proves an archive install and `hammunition-console --version` before publishing.

- **Not yet verified.** The bench run on the field laptop has not happened: no real `hammunition install` has been driven through the Install pane on a real target, urwid's `urwid.Terminal` has not been run against a real engine install on any machine, and Raspberry Pi OS, Pop!_OS and Mint are inferred from their bases. The per-profile installed state and the retired-units report were built against recorded fixtures and show "unknown" when the engine does not supply them. The README's Status section says the same.

- The engine floor is 0.20.0: the release that carries `list --json` members with installed sizes (E1) and retired units in `update --json` (E2), both of which the Install and Update screens read.

- CI and release now call the reusable workflows in `ChiefGyk3D/git-your-ship-together` v1.6.3 (`python-ci`, `bash-ci`, `security`, `artifact-release`), pinned by commit; the archive-install proofs, the urwid 2.6.16 leg and the changelog-fragment check stay local, and the release adds signatures and build provenance beside `SHA256SUMS`.

