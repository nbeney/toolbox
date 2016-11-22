# Prevent us being sourced multiple times.
if [ "${TBX_INC_PROMPT}" == "sourced" ]; then
    #echo "Already sourced: prompt.sh"
    return
else
    #echo "Sourcing prompt.sh"
    TBX_INC_PROMPT="sourced"
fi

# Dependencies.
. ~/toolbox/etc/.bashrc.d/ansi.sh

function __tbx_start_timer
{
    TBX_START_SECONDS=${TBX_START_SECONDS:-${SECONDS}}
}

function __tbx_stop_timer
{
    TBX_DURATION=$((${SECONDS} - ${TBX_START_SECONDS}))
    unset TBX_START_SECONDS
}

trap __tbx_start_timer DEBUG

__tbx_set_prompt()
{
    local last_rc=$?
    __tbx_stop_timer

    local RESET="\[${TBX_ANSI_RESET}\]"
    local WHITE="\[${TBX_ANSI_FG_WHITE}\]"
    local COL_ALERT="\[${TBX_ANSI_FG_RED}\]"
    local COL_NORMAL="\[${TBX_ANSI_FG_GREEN}\]"
    local COL_NEUTRAL="\[${TBX_ANSI_FG_YELLOW}\]"
    local COL_1="\[${TBX_ANSI_FG_CYAN}\]"
    local COL_2="\[${TBX_ANSI_FG_PURPLE}\]"

    PS1="\n${COL_2}\D{%Y%m%d-%H:%M:%S} "

    # Current user, host and level
    if [ -f /prod/cbtech/bin/cbcfg ]; then
	local LEVEL=$(/prod/cbtech/bin/cbcfg LEVEL)
        if [ "${LEVEL}" == "dev" ]; then
            local color="${COL_NORMAL}"
        else
            local color="${COL_ALERT}"
        fi
	PS1+="${COL_1}\u${WHITE}@${COL_1}\h ${WHITE}[${color}${LEVEL}${WHITE}] "
    else
        PS1+="${COL_1}\u${WHITE}@${COL_1}\h "
    fi

    # Current directory
    PS1+="${COL_1}\w "

    # Current branch
    local BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [ -n "${BRANCH}" ]; then
	local DIRTY=$(git status --porcelain 2>/dev/null)
	if [ -z "${DIRTY}" ]; then
            local color="${COL_NORMAL}"
	else
            local color="${COL_ALERT}"
            BRANCH+="*"
	fi
	PS1+="${WHITE}(${color}${BRANCH}${WHITE}) "
    fi
    
    # Return code of last command
    if [[ ${last_rc} == 0 ]]; then
        local color="${COL_NORMAL}"
    else
        local color="${COL_ALERT}"
    fi
    PS1+="${WHITE}RC=${color}${last_rc} "

    # Last command duration
    PS1+="${WHITE}T=${COL_NEUTRAL}${TBX_DURATION}s "
    
    # Number of background jobs
    if [ -z "$(jobs | egrep -v ' Done | Exit | Terminated ')" ]; then
        local color="${COL_NORMAL}"
    else
        local color="${COL_ALERT}"
    fi
    PS1+="${WHITE}J=${color}\j "

    # Virtual env
    local VENV=$(basename "${VIRTUAL_ENV}")
    if [ -n "${VENV}" ]; then
        PS1+="${WHITE}{${COL_NORMAL}${VENV}${WHITE}} "
    fi

    # Final ANSI reset.
    PS1+="\n${WHITE}\$ ${RESET}"
}

PROMPT_COMMAND='__tbx_set_prompt'
