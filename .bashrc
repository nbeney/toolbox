# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# don't put duplicate lines or lines starting with space in the history.
# See bash(1) for more options
HISTCONTROL=ignoreboth

# append to the history file, don't overwrite it
shopt -s histappend

shopt -s completion_strip_exe

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
HISTSIZE=1000
HISTFILESIZE=2000

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# If set, the pattern "**" used in a pathname expansion context will
# match all files and zero or more directories and subdirectories.
#shopt -s globstar

# make less more friendly for non-text input files, see lesspipe(1)
#[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
	# We have color support; assume it's compliant with Ecma-48
	# (ISO/IEC-6429). (Lack of such support is extremely rare, and such
	# a case would tend to support setf rather than setaf.)
	color_prompt=yes
    else
	color_prompt=
    fi
fi

if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w \$\[\033[00m\] '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi
unset color_prompt force_color_prompt

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
*)
    ;;
esac

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    #alias dir='dir --color=auto'
    #alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# colored GCC warnings and errors
#export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'

# some more ls aliases
#alias ll='ls -l'
#alias la='ls -A'
#alias l='ls -CF'

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

# Added by Nicolas Beney

export PATH=/home/pi/tools/bin:${PATH}

export PYTHONSTARTUP=/home/pi/tools/python/startup.py

for dir in ~/venvs/*; do
    alias ve-$(basename ${dir})=". ${dir}/bin/activate"
done

alias s=sudo
alias sac="sudo apt-cache"
alias sag="sudo apt-get"
alias ss="sudo service"
alias sss="sudo service --status-all"
alias sst="sudo samba-tool"


#======================================================================================================================
# From https://gitlab.com/gitforteams/gitforteams/blob/master/resources/sample-bash_profile.md
#======================================================================================================================

# git branch autocompletion
if [ -f ~/.git-completion.bash ]; then
    . ~/.git-completion.bash
fi

RESET='$(tput sgr0)'
BOLD='$(tput bold)'

FG_BLACK='$(tput setaf 0)'
FG_RED='$(tput setaf 1)'
FG_GREEN='$(tput setaf 2)'
FG_YELLOW='$(tput setaf 3)'
FG_BLUE='$(tput setaf 4)'
FG_PURPLE='$(tput setaf 5)'
FG_CYAN='$(tput setaf 6)'
FG_WHITE='$(tput setaf 7)'

set_prompt()
{
    local last_rc=$?

    PS1="${FG_WHITE}"

    # Current user
    PS1+="${FG_YELLOW}\u${FG_WHITE}@"

    # Host name (short)
    PS1+="${FG_GREEN}\h"

    # Current level
    if [ -f /prod/cbtech/bin/cbcfg ]; then
	local LEVEL=${/prod/cbtech/bin/cbcfg LEVEL}
	PS1+="${FG_WHITE}[${FG_PURPLE}${LEVEL}${FG_WHITE}] "
    else
	PS1+=" "
    fi

    # Current directory
    PS1+="${FG_CYAN}\w "

    # Current branch
    local BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [ -n "${BRANCH}" ]; then
	local DIRTY=$(git status --porcelain 2>/dev/null)
	if [ -n "${DIRTY}" ]; then
	    PS1+="${FG_WHITE}(${FG_RED}${BRANCH}${FG_WHITE}) "
	else
	    PS1+="${FG_WHITE}(${FG_YELLOW}${BRANCH}${FG_WHITE}) "
	fi
    fi

    
    # Number of background jobs
    if [ -n "$(jobs | egrep -v ' Done | Exit ')" ]; then
        PS1+="${FG_PURPLE}J=\j "
    fi

    # Return code of last command
    if [[ ${last_rc} != 0 ]]; then
        PS1+="${FG_RED}RC=${last_rc} "
    fi

    PS1+="\n${FG_WHITE}\$ "
}

PROMPT_COMMAND='set_prompt'
