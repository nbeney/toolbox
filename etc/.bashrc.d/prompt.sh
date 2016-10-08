# Prevent us being sourced multiple times.
if [ ${TOOLBOX_INC_PROMPT:-unset} == "unset" ]; then
    echo "Sourcing prompt.sh"
    export TOOLBOX_INC_PROMPT=1
else
    echo "Already sourced: prompt.sh"
    return
fi

# Dependencies.
. ~/toolbox/etc/.bashrc.d/ansi.sh

function tlc_start_timer
{
    TLC_START_SECONDS=${TLC_START_SECONDS:-${SECONDS}}
}

function tlc_stop_timer
{
    TLC_DURATION=$((${SECONDS} - ${TLC_START_SECONDS}))
    unset TLC_START_SECONDS
}

trap tlc_start_timer DEBUG

set_prompt()
{
    local last_rc=$?
    tlc_stop_timer

    local RESET="\[${ANSI_RESET}\]"
    local WHITE="\[${ANSI_FG_WHITE}\]"
    local COL_ALERT="\[${ANSI_FG_RED}\]"
    local COL_NORMAL="\[${ANSI_FG_GREEN}\]"
    local COL_NEUTRAL="\[${ANSI_FG_YELLOW}\]"
    local COL_1="\[${ANSI_FG_CYAN}\]"
    local COL_2="\[${ANSI_FG_PURPLE}\]"

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
    PS1+="${WHITE}T=${COL_NEUTRAL}${TLC_DURATION}s "
    
    # Number of background jobs
    if [ -z "$(jobs | egrep -v ' Done | Exit | Terminated ')" ]; then
        local color="${COL_NORMAL}"
    else
        local color="${COL_ALERT}"
    fi
    PS1+="${WHITE}J=${color}\j "

    PS1+="\n${WHITE}\$ ${RESET}"
}

PROMPT_COMMAND='set_prompt'
