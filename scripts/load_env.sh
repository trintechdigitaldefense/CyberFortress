#!/usr/bin/env bash
# Safely load CyberFortress key/value configuration without executing .env content.
load_cyberfortress_env() {
  local env_file="${1:-.env}"
  local line key value
  [[ -f "$env_file" ]] || return 0

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    [[ -z "$line" || "$line" == \\#* ]] && continue
    if [[ "$line" =~ ^(CF_[A-Za-z0-9_]+)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      value="${BASH_REMATCH[2]}"
      if [[ "$value" == \"*\" && "${#value}" -ge 2 ]]; then
        value="${value:1:${#value}-2}"
      elif [[ "$value" == \'*\' && "${#value}" -ge 2 ]]; then
        value="${value:1:${#value}-2}"
      fi
      export "$key=$value"
    fi
  done < "$env_file"
}
