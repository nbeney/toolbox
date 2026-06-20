# Kiro CLI pre block. Keep at the top of this file.
[[ -f "${HOME}/.local/share/kiro-cli/shell/bashrc.pre.bash" ]] && builtin source "${HOME}/.local/share/kiro-cli/shell/bashrc.pre.bash"

# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

#==============================================================================
# Shell options
#==============================================================================

# Don't put duplicate lines or lines starting with space in the history
HISTCONTROL=ignoreboth

# Append to the history file, don't overwrite it
shopt -s histappend

# History length
HISTSIZE=1000
HISTFILESIZE=2000

# Check the window size after each command and update LINES and COLUMNS
shopt -s checkwinsize

# "**" matches all files and zero or more directories/subdirectories
#shopt -s globstar

# Case-insensitive tab completion
bind 'set completion-ignore-case on'

#==============================================================================
# Environment
#==============================================================================

export PAGER=less
export EDITOR='emacs -nw'
export TERM=xterm-256color
export LC_COLLATE=en_GB.utf8

export PATH="${HOME}/scripts:$PATH"
export PATH="${HOME}/.local/bin:$PATH"

# ANSI foreground color codes (for use in scripts/prompts)
export FGCOLOR_BLACK=30
export FGCOLOR_RED=31
export FGCOLOR_GREEN=32
export FGCOLOR_YELLOW=33
export FGCOLOR_BLUE=34
export FGCOLOR_MAGENTA=35
export FGCOLOR_CYAN=36
export FGCOLOR_WHITE=37

export S_COLORS=auto

umask 0022

#==============================================================================
# Prompt
#==============================================================================

# Set variable identifying the chroot you work in
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# Set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color|*-256color) color_prompt=yes;;
esac

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
        color_prompt=yes
    else
        color_prompt=
    fi
fi

if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi
unset color_prompt force_color_prompt

# If this is an xterm, set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
esac

#==============================================================================
# Completion
#==============================================================================

if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

[ -f ~/.git-completion.bash ] && . ~/.git-completion.bash

complete -C '/usr/local/bin/aws_completer' aws

#==============================================================================
# Lesspipe / dircolors
#==============================================================================

[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
fi

#==============================================================================
# Aliases — navigation
#==============================================================================

alias cd-repos="cd ~/repos"
for _dir in ~/repos/*/; do
    _name=$(basename "${_dir}")
    alias "cd-${_name}=cd ${_dir}"
done
unset _dir _name

alias ~="cd ~"
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."
alias .....="cd ../../../.."

alias ..1="cd .."
alias ..2="cd ../.."
alias ..3="cd ../../.."
alias ..4="cd ../../../.."
alias ..5="cd ../../../../.."
alias ..6="cd ../../../../../.."
alias ..7="cd ../../../../../../.."
alias ..8="cd ../../../../../../../.."
alias ..9="cd ../../../../../../../../.."

#==============================================================================
# Aliases — file listing
#==============================================================================

alias ls='ls --color=auto'
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias llt='ls -lt --color=auto'
alias lltr='ls -ltr --color=auto'

# Open the most recently modified file(s) in less
alias lll='less $(ls -1tr | tail -1)'
alias lll2='less $(ls -1tr | tail -2)'
alias lll3='less $(ls -1tr | tail -3)'
alias lll4='less $(ls -1tr | tail -4)'
alias lll5='less $(ls -1tr | tail -5)'

alias dush='du -csh * | sort -h'

#==============================================================================
# Aliases — grep / search
#==============================================================================

alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

alias rg="rg --colors='match:fg:black' --colors='match:bg:yellow' --colors='line:fg:cyan' --colors='path:fg:green'"

#==============================================================================
# Aliases — text processing
#==============================================================================

alias h="head -n"
alias pandoc-html="pandoc --to=html --standalone --self-contained"
alias suc='sort | uniq -c'
alias sucn='sort | uniq -c | sort -n'
alias sucnr='sort | uniq -c | sort -nr'
alias split-fix="tr '\01' \\n"

# Prepend a timestamp to each line of stdin
alias ts="awk '{ print strftime(\"[%Y-%m-%d %H:%M:%S]\"), \$0; fflush(); }'"

#==============================================================================
# Aliases — system
#==============================================================================

alias ps='ps auxf'
alias cls=clear
alias cal="ncal -M -b"
alias xemacs='emacs -nw'
alias config="xemacs ~/.bashrc && . ~/.bashrc"

alias sa="sudo apt"
alias sag="sudo apt-get"
alias ssn="sudo snap"
alias ssc="sudo systemctl"
alias sys-suspend="sudo systemctl suspend"

# Alert for long-running commands: sleep 10; alert
alias alert='notify-send --urgency=low -i "$([ $? = 0 ] && echo terminal || echo error)" "$(history|tail -n1|sed -e '\''s/^\s*[0-9]\+\s*//;s/[;&|]\s*alert$//'\'')"'

#==============================================================================
# Aliases — git
#==============================================================================

alias ga="git add"
alias gb="git branch"
alias gba="git branch -a"
alias gc="git commit"
alias gco="git checkout"
alias gd=__git_diff
alias gl="git log --oneline"
alias gld="git log-gdo"
alias gri="git rebase -i HEAD~15"
alias grv="git remote -v"
alias gs="git status"
alias gs1="git status1"
alias gss="git status --short"
alias gsa="git status-all"
alias gt='git tag --format='\''%(creatordate:short)%09%(*objectname:short)%(objectname)%09%(refname:strip=2)'\'' | sort'

alias galiases="alias | grep git | grep -v galiases"
alias lg="lazygit"

#==============================================================================
# Aliases — AWS CLI
#==============================================================================

alias awsa="aws --output table"
alias awsj="aws --output json"
alias awsx="aws --output text"
alias awsy="aws --output yaml"
alias awsys="aws --output yaml-stream"

#==============================================================================
# Aliases — uvx tools
#==============================================================================

alias flet="uvx flet"
alias glances="uvx glances"
alias marimo="uvx marimo"
alias mpr="uvx mpremote"
alias nicegui-pack="uvx --from nicegui nicegui-pack"
alias ruff="uvx ruff"
alias streamlit="uvx streamlit"
alias thonny="uvx thonny"

#==============================================================================
# Aliases — todo
#==============================================================================

alias td=todo
alias tdl=todo-loop
alias todo='task-todo.sh'
alias todo-loop='task-loop.sh'

#==============================================================================
# Functions
#==============================================================================

# Simple calculator: ? 2 + 2
function ?() { echo "$*" | bc; }

# git diff with colour paging, or pass args through
function __git_diff() {
    if [ $# -eq 0 ]; then
        git diff --color | less -Rp '^diff.*'
    else
        git diff "$@"
    fi
}

# Repeat a command N times: repeat 5 echo hello
function repeat() {
    local n=$1
    shift
    for ((i=n; i--; )); do
        "$@"
    done
}

#==============================================================================
# External files
#==============================================================================

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

if [ -f "${HOME}/.deno/env" ]; then
    . "${HOME}/.deno/env"
fi
if [ -f "${HOME}/.deno-completions" ]; then
    . "${HOME}/.deno-completions"
fi

[[ "$TERM_PROGRAM" == "kiro" ]] && . "$(kiro --locate-shell-integration-path bash)"


# Kiro CLI post block. Keep at the bottom of this file.
[[ -f "${HOME}/.local/share/kiro-cli/shell/bashrc.post.bash" ]] && builtin source "${HOME}/.local/share/kiro-cli/shell/bashrc.post.bash"
