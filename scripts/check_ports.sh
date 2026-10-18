#!/usr/bin/env bash
# scripts/check_ports.sh - list and validate host ports against ports.env
#
# Usage: scripts/check_ports.sh   (or: make ports)
#
# Prints every host port (from ports.env) with the compose files that publish it,
# and fails (exit 1) when:
#   - ports.env has a malformed line, a duplicate name or a duplicate port
#   - a compose file publishes a hardcoded host port ("8080:8080")
#   - a compose file gives a host port a fallback default (${X_HOST_PORT:-...})
#   - a compose file uses a *_HOST_PORT variable that ports.env doesn't define
#   - ports.env defines a port that no compose file uses
set -uo pipefail

cd "$(dirname "$0")/.."
REGISTRY=ports.env
errors=0
err() { echo "ERROR: $*" >&2; errors=$((errors + 1)); }

[ -f "$REGISTRY" ] || { echo "ERROR: $REGISTRY not found" >&2; exit 1; }

# --- registry ----------------------------------------------------------------
declare -A port_of name_of
while IFS= read -r line || [ -n "$line" ]; do
  line="${line%$'\r'}"
  [[ -z "${line//[[:space:]]/}" || "$line" =~ ^[[:space:]]*# ]] && continue
  if [[ ! "$line" =~ ^([A-Z0-9_]+_HOST_PORT)=([0-9]+)$ ]]; then
    err "$REGISTRY: malformed line (expected NAME_HOST_PORT=<number>): $line"; continue
  fi
  name="${BASH_REMATCH[1]}"; port="${BASH_REMATCH[2]}"
  [ -n "${port_of[$name]:-}" ] && err "$REGISTRY: $name defined twice"
  [ -n "${name_of[$port]:-}" ] && err "$REGISTRY: port $port used by both ${name_of[$port]} and $name"
  port_of[$name]=$port; name_of[$port]=$name
done < "$REGISTRY"

# --- compose files -------------------------------------------------------------
mapfile -t files < <(find . \( -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' \) \
  -not -path '*/node_modules/*' -not -path './.git/*' | sed 's#^\./##' | sort)

declare -A used_in
for f in "${files[@]}"; do
  while IFS= read -r hit; do
    lineno="${hit%%:*}"; text="${hit#*:}"
    [[ "$text" =~ ^[[:space:]]*# ]] && continue
    err "$f:$lineno hardcoded host port - use \"\${<NAME>_HOST_PORT:?see ports.env}:<container port>\": ${text#"${text%%[![:space:]]*}"}"
  done < <(grep -nE '^[[:space:]]*-[[:space:]]*"?[0-9]+:[0-9]+' "$f")
  while IFS= read -r hit; do
    err "$f:${hit%%:*} host port has a fallback default - use :? so it fails fast"
  done < <(grep -nE '_HOST_PORT:-' "$f")
  while IFS= read -r name; do
    used_in[$name]+="${used_in[$name]:+, }$f"
  done < <(grep -oE '\$\{[A-Z0-9_]+_HOST_PORT' "$f" | sed 's/^\${//' | sort -u)
done

for name in "${!used_in[@]}"; do
  [ -n "${port_of[$name]:-}" ] || err "$name is used in ${used_in[$name]} but not defined in $REGISTRY"
done
for name in "${!port_of[@]}"; do
  [ -n "${used_in[$name]:-}" ] || err "$REGISTRY: $name=${port_of[$name]} is not used by any compose file"
done

# --- report --------------------------------------------------------------------
printf '%-6s  %-34s  %s\n' PORT VARIABLE "PUBLISHED BY"
for port in $(printf '%s\n' "${!name_of[@]}" | sort -n); do
  name="${name_of[$port]}"
  printf '%-6s  %-34s  %s\n' "$port" "$name" "${used_in[$name]:--}"
done

if [ "$errors" -gt 0 ]; then
  echo "" >&2; echo "$errors problem(s) found" >&2; exit 1
fi
echo ""; echo "OK: ${#port_of[@]} host ports, no duplicates, all defined and used."
