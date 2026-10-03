#!/bin/sh
# SPDX-FileCopyrightText: Copyright (C) 2026 Renegade Penguin LLC
# SPDX-License-Identifier: GPL-3.0-or-later
# Remove what install.sh placed.
#
#   ./uninstall.sh                 from ~/.local
#   ./uninstall.sh --prefix DIR    from DIR (absolute path)
#
# The wrapper is removed only when it carries install.sh's mark. The console's own
# configuration, ~/.config/hammunition-console/config.toml, is left in place.
set -eu

prefix="${HOME}/.local"
while [ $# -gt 0 ]; do
    case "$1" in
        --prefix)
            [ $# -ge 2 ] || { echo "--prefix needs a directory" >&2; exit 2; }
            prefix="$2"
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
case "${prefix}" in /*) ;; *) echo "--prefix must be an absolute path, got: ${prefix}" >&2; exit 2 ;; esac

share="${prefix}/share/hammunition-console"
wrapper="${prefix}/bin/hammunition-console"
man="${prefix}/share/man/man1/hammunition-console.1"
mark="# Installed by hammunition-console install.sh."

# A symlinked share directory points into a tree this script did not make.
if [ -L "${share}" ]; then
    echo "${share} is a symbolic link; left in place."
else
    rm -rf "${share}/hammunition_console"
    rmdir "${share}" 2>/dev/null || true
fi
rm -f "${man}"
if [ -e "${wrapper}" ] || [ -L "${wrapper}" ]; then
    if grep -qxF "${mark}" "${wrapper}" 2>/dev/null; then
        rm -f "${wrapper}"
    else
        echo "${wrapper} was not written by this installer; left in place."
    fi
fi
echo "Removed hammunition-console. Its configuration, ~/.config/hammunition-console/config.toml, was left in place."
