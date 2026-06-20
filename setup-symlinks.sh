#!/usr/bin/env bash
# setup-symlinks.sh — create or update symlinks to toolbox files.
# Run this when setting up a new dev environment.

set -euo pipefail

TOOLBOX="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

log_info()    { echo -e "${CYAN}INFO${RESET}:  $*"; }
log_warning() { echo -e "${YELLOW}WARN${RESET}:  $*"; }
log_error()   { echo -e "${RED}ERROR${RESET}: $*"; }

create_symlink() {
    local target="${1}"   # file in toolbox (the real file)
    local link="${2}"     # symlink to create
    local parent
    parent="$(dirname "${link}")"

    # Create parent directory if needed
    if [[ ! -d "${parent}" ]]; then
        mkdir -p "${parent}"
        log_info "created directory: ${BOLD}${parent}${RESET}"
    fi

    # Target doesn't exist in toolbox — warn and skip
    if [[ ! -e "${target}" ]]; then
        log_error "target not found, skipping: ${BOLD}${link} -> ${target}${RESET}"
        return
    fi

    # Symlink already exists
    if [[ -L "${link}" ]]; then
        local current_target
        current_target="$(readlink "${link}")"
        if [[ "${current_target}" == "${target}" ]]; then
            log_info "already up to date: ${BOLD}${link}${RESET} -> ${target}"
        else
            ln -sf "${target}" "${link}"
            log_info "updated: ${BOLD}${link}${RESET} -> ${target} (was -> ${current_target})"
        fi
        return
    fi

    # Regular file exists — back it up
    if [[ -e "${link}" ]]; then
        mv "${link}" "${link}.bak"
        log_warning "back up regular file: ${BOLD}${link}${RESET} -> ${link}.bak"
    fi

    ln -s "${target}" "${link}"
    log_info "created symlink: ${BOLD}${link}${RESET} -> ${target}"
}

echo
echo -e "${BOLD}Setting up symlinks${RESET} (toolbox: ${CYAN}${TOOLBOX}${RESET})"
echo

create_symlink "${TOOLBOX}/.bashrc"                            "${HOME}/.bashrc"
create_symlink "${TOOLBOX}/.tmux.conf"                         "${HOME}/.tmux.conf"
create_symlink "${TOOLBOX}/scripts"                            "${HOME}/scripts"
create_symlink "${TOOLBOX}/.kiro/steering/coding-standards.md" "${HOME}/.kiro/steering/coding-standards.md"

echo
echo -e "${BOLD}Done.${RESET}"
echo
