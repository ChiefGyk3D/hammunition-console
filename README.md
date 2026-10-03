# hammunition-console

A full-screen terminal front end for the [Hammunition](https://github.com/ChiefGyk3D/Hammunition) engine. It shows what is
installed, what is wrong and what to do next, and runs the engine's own commands for you, so a licensed operator can get from
a fresh machine to a working station without remembering the CLI's verbs. It runs in a terminal; whether it works well over SSH or on a Raspberry Pi has not been measured.

It is a client of the engine, not part of it: it has no install logic, no package names and no catalog parser. It asks the engine.

## What it is

Six screens: Home, Install, Station, Logs, Update and Help. Every action is a command you could type yourself, and the console
shows it before it runs. Hardware setup is one first-run step on Home (`hammunition hardware apply`, in a pane, with the
engine's own prompts); everything else about hardware, and maps, is left to the CLI and to
[hammunition-tray](https://github.com/ChiefGyk3D/hammunition-tray) for now.

## Requirements

- Hammunition 0.19.0 or later on `PATH` (the engine's `--json` interface, D-059). Install it first; this console never installs it.
- Python 3.11 or later and `python3-urwid` 2.6 or later. Measured archive versions: Debian 13 and Parrot 2.6.16, Ubuntu 24.04
  2.6.10, Ubuntu 26.04 and Kali 3.0.4.
- A terminal of at least 80x24. It refuses to start without a terminal, with `TERM=dumb`, or as root.

## Install

Through Hammunition, once a release is cataloged:

```sh
hammunition install hammunition-console
```

From a checkout, for your own account, with no pip and no virtualenv:

```sh
sudo apt install python3-urwid
./install.sh            # into ~/.local; --prefix DIR and --interpreter PATH are the options
hammunition-console
```

`./uninstall.sh` removes what `install.sh` placed and leaves `~/.config/hammunition-console/` alone. To try it without
installing, `python3 -m hammunition_console` from the checkout works.

## How it works

Three channels, each with one job.

1. **Reads** run `hammunition <verb> --json` in a worker thread and parse the one document it prints. The console reads only
   the verbs listed in [docs/contract.md](docs/contract.md), refuses a document whose `schema` it does not know, and reads the
   engine's version from the first document's `engine` field.
2. **Writes** run the real `hammunition` command inside a terminal pane. The child owns the tty: sudo's password prompt, the
   group choice and any consent prompt reach the engine untouched, typed by you. The console sees only the exit code, then
   reads again.
3. **Its own config**, `~/.config/hammunition-console/config.toml`: the last screen, the colour theme, whether you dismissed
   the first-run checklist. Nothing else. (A crash writes `crash.log` beside it with the exception type and its frames, never a
   message.)

The plan always comes first: choosing a profile shows the engine's own dry run (`--dry-run`), grouped as the engine groups it,
and nothing runs until you press `R` on it.

## What it never does

- It never answers a consent prompt for you: you type yes into the engine's own prompt, in the pane.
- It never runs anything but the engine's own commands (and the apt upgrade the engine's update report offers).
- It never stores your callsign, grid square or any station value; the engine's station file is the only copy.
- It never fetches anything from the network itself; the engine does, and it asks GitHub, git hosts and PyPI only when you press u on Update.

Also: it never passes the engine's assume-yes flag, never sets a scripted-consent environment variable and removes any you
exported from the environment of everything it starts, never runs a `doctor` fix (it shows the engine's fix text and leaves the
command to you), and never runs as root. The header says only "station: set" or "not set", and the Station screen hides
values until you ask.

## Keys

| Keys | Meaning |
|---|---|
| `1-5` | open the screen with that number (Home) |
| `Enter` | open the selected row |
| `b / Esc` | go back; changes nothing (in a text prompt only Esc: b is typed) |
| `?` | help |
| `q` | quit |
| `r` | refresh this screen |
| `R` | run the planned command in a terminal pane (plan and confirm screens) |
| `Tab` | switch between profiles and single units (Install) |
| `U` | plan an uninstall of the selected profile (Install) |
| `i` | the selected profile's documentation (Install) |
| `v` | reveal or hide station values (Station) |
| `c` | clear the selected value, where the engine can (Station) |
| `u` | also ask upstream whether the catalog's pins are current (Update) |
| `A` | run the apt upgrade the report offers (Update) |
| `B` | plan the rebuilds the report offers (Update) |
| `s` | skip the selected first-run step (Home) |
| `D` | dismiss the first-run checklist (Home) |

## Screens

- **Home**: the engine's health check, whether the station is set, the last run, units behind their pin, and a first-run
  checklist (set the station, apply the hardware rules, pick a profile, install it).
- **Install**: profiles, and with `Tab` single units; the plan; the run.
- **Station**: the saved values, changed by running the engine's own `station set`.
- **Logs**: each run the engine recorded, newest first; a run in progress is followed live.
- **Update**: installed against the catalog; `u` also asks upstream.
- **Help**: keys, what the console never does, and what each profile is for.

## Status

First release. What has run: the test suite (unit tests against fixtures recorded from the engine, a fake `hammunition` that
asks for `yes` on a real pseudo-terminal, and the console driven end to end in one) on Python 3.13 with urwid 2.6.16. The
CI matrix also names Python 3.11 with urwid 2.6.10, urwid 3.0.4, and the Debian 13 and Ubuntu 24.04 archives' own
`python3-urwid`; those jobs are unmeasured until CI has run them.

What has not been run: a real `hammunition install` through the pane on a real target; urwid's `urwid.Terminal` against a
real engine install on any machine; the engine's per-profile installed state and its `update` report for retired units
(engine work E1 and E2) were built against recorded fixtures, so each screen that reads them shows "unknown" when they are
absent; Raspberry Pi OS, Pop!_OS and Mint are inferred from their bases, not run. A claim about hardware belongs here only after
it has run there.

## Development

```sh
python3 -m venv --system-site-packages .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python3 -m pytest          # also: ruff check . ; mypy ; python3 scripts/spdx.py --check
```

`--system-site-packages` lets the venv use the distribution's `python3-urwid`; to test another urwid, `pip install "urwid==X"`
into the venv. Fixtures are recorded by `scripts/capture_fixtures.py` from a real engine on a throwaway home with the station
set to `N0TST` and `FN31pr`, scrubbed, and scanned for identifiers; review every new fixture by eye before committing.

`tests/test_verbs.py` checks the console's verb list against the engine's `docs/reference/json-interface.md`. That check is
opt-in: `export HAMMUNITION_ENGINE_ROOT=/path/to/your/Hammunition/checkout` before running pytest, otherwise it is skipped
and says why.

CI is the maintainer's reusable workflows in `ChiefGyk3D/git-your-ship-together` (GYST), pinned by commit: `ci.yml` calls
`python-ci.yml` (ruff, `mypy --strict`, `scripts/spdx.py --check`, pytest on Python 3.11 with urwid 2.6.10 and on 3.13 with
urwid 3.0.4) and `bash-ci.yml` (shellcheck over `install.sh`, `uninstall.sh` and `bin/hammunition-console`); `security.yml`
calls `security.yml` (CodeQL, gitleaks, Semgrep, dependency review, Scorecard; no Doppler); `release.yml` calls
`artifact-release.yml`. What stays in this repository's own `ci.yml` is what a shared workflow cannot do: the urwid 2.6.16
leg, the two archive-install proofs (Debian 13 and Ubuntu 24.04 containers running `install.sh` as an unprivileged user
against the archive's `python3-urwid`) and the changelog-fragment check.

Required checks on `main`: `ci / CI green`, `shell / CI green`, `local jobs green`, and the jobs of the `Security` workflow
(`security / ...`). `Release` builds and verifies on a pull request and publishes only on a `v*` tag.

A check is trusted only after you have broken the thing it watches and seen it fail with a message that names the fix. Never
edit `CHANGELOG.md` in a pull request: add `changelog.d/<pr>.<kind>.md`.

## Licence

GPL-3.0-or-later. Copyright Renegade Penguin LLC.
