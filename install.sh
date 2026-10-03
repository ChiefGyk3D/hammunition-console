#!/bin/sh
# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
# Install hammunition-console for the current user (or into --prefix).
#
# The script is deliberately NOT run as root and uses no pip and no virtualenv: it
# copies the package, writes a /bin/sh wrapper that runs the system Python, and
# copies the man page. Nothing is fetched.
#
#   ./install.sh                      into ~/.local
#   ./install.sh --prefix DIR         into DIR (absolute path)
#   ./install.sh --interpreter PATH   the Python the wrapper runs (default
#                                     /usr/bin/python3); it must be 3.11 or later
#                                     and import urwid (Debian family:
#                                     sudo apt install python3-urwid)
#
# Files placed:
#   <prefix>/share/hammunition-console/hammunition_console/   the package
#   <prefix>/bin/hammunition-console                          the wrapper
#   <prefix>/share/man/man1/hammunition-console.1             the man page
# Remove them with ./uninstall.sh. The console's own configuration
# (~/.config/hammunition-console/) is never touched by either script.
set -eu

prefix="${HOME}/.local"
interpreter=/usr/bin/python3

while [ $# -gt 0 ]; do
    case "$1" in
        --prefix)
            [ $# -ge 2 ] || { echo "--prefix needs a directory" >&2; exit 2; }
            prefix="$2"
            shift
            ;;
        --interpreter)
            [ $# -ge 2 ] || { echo "--interpreter needs a path" >&2; exit 2; }
            interpreter="$2"
            shift
            ;;
        -h | --help)
            sed -n '4,/^set -eu/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
    esac
    shift
done

if [ "$(id -u)" -eq 0 ]; then
    echo "Do not run this as root: it installs for your own account." >&2
    exit 1
fi
case "${prefix}" in /*) ;; *) echo "--prefix must be an absolute path, got: ${prefix}" >&2; exit 2 ;; esac
case "${interpreter}" in /*) ;; *) echo "--interpreter must be an absolute path, got: ${interpreter}" >&2; exit 2 ;; esac
[ -x "${interpreter}" ] || { echo "--interpreter ${interpreter} is not an executable file." >&2; exit 2; }
"${interpreter}" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null \
    || { echo "${interpreter} is not Python 3.11 or later." >&2; exit 1; }
"${interpreter}" -c 'import urwid' 2>/dev/null \
    || { echo "${interpreter} cannot import urwid. Debian family: sudo apt install python3-urwid" >&2; exit 1; }

src="$(cd "$(dirname "$0")" && pwd)"
share="${prefix}/share/hammunition-console"
wrapper="${prefix}/bin/hammunition-console"
man="${prefix}/share/man/man1/hammunition-console.1"
mark="# Installed by hammunition-console install.sh."

# Never write through a symlink into a tree this script did not make.
for path in "${share}" "${share}/hammunition_console" "${wrapper}" "${man}"; do
    if [ -L "${path}" ] && ! { [ "${path}" = "${wrapper}" ] && grep -qxF "${mark}" "${wrapper}" 2>/dev/null; }; then
        echo "${path} is a symbolic link; not followed, nothing installed." >&2
        exit 1
    fi
done
if [ -e "${wrapper}" ] && ! grep -qxF "${mark}" "${wrapper}"; then
    echo "${wrapper} exists and was not written by this installer; not replaced." >&2
    exit 1
fi

rm -rf "${share}/hammunition_console"
install -d -m 0755 "${share}" "${prefix}/bin" "${prefix}/share/man/man1"
cp -R "${src}/hammunition_console" "${share}/hammunition_console"
find "${share}" -name __pycache__ -type d -prune -exec rm -rf {} +
cat >"${wrapper}" <<WRAP
#!/bin/sh
${mark}
PYTHONPATH="${share}\${PYTHONPATH:+:\$PYTHONPATH}"
export PYTHONPATH
exec "${interpreter}" -P -m hammunition_console "\$@"
WRAP
chmod 0755 "${wrapper}"
install -m 0644 "${src}/man/hammunition-console.1" "${man}"

echo "Installed hammunition-console."
echo "  package  ${share}/hammunition_console"
echo "  command  ${wrapper}"
echo "  man page ${man}"
case ":${PATH}:" in *":${prefix}/bin:"*) ;; *) echo "Note: ${prefix}/bin is not on your PATH." ;; esac
