# Prevent us being sourced multiple times.
if [ "${TBX_INC_ANSI}" == "sourced" ]; then
    #echo "Already sourced: ansi.sh"
    return
else
    #echo "Sourcing ansi.sh"
    TBX_INC_ANSI="sourced"
fi

export TBX_ANSI_BLINK=$(tput blink)
export TBX_ANSI_BOLD=$(tput bold)
export TBX_ANSI_DIM=$(tput dim)
export TBX_ANSI_INVIS=$(tput invis)
export TBX_ANSI_RESET=$(tput sgr0)
export TBX_ANSI_REVERSE=$(tput rev)
export TBX_ANSI_STANDOUT_START=$(tput smso)
export TBX_ANSI_STANDOUT_STOP=$(tput rmso)
export TBX_ANSI_UNDER_START=$(tput smul)
export TBX_ANSI_UNDER_STOP=$(tput rmul)

export TBX_ANSI_FG_BLACK=$(tput setaf 0)
export TBX_ANSI_FG_RED=$(tput setaf 1)
export TBX_ANSI_FG_GREEN=$(tput setaf 2)
export TBX_ANSI_FG_YELLOW=$(tput setaf 3)
export TBX_ANSI_FG_BLUE=$(tput setaf 4)
export TBX_ANSI_FG_PURPLE=$(tput setaf 5)
export TBX_ANSI_FG_CYAN=$(tput setaf 6)
export TBX_ANSI_FG_WHITE=$(tput setaf 7)
export TBX_ANSI_FG_DEFAULT=$(tput setaf 9)

export TBX_ANSI_BG_BLACK=$(tput setab 0)
export TBX_ANSI_BG_RED=$(tput setab 1)
export TBX_ANSI_BG_GREEN=$(tput setab 2)
export TBX_ANSI_BG_YELLOW=$(tput setab 3)
export TBX_ANSI_BG_BLUE=$(tput setab 4)
export TBX_ANSI_BG_PURPLE=$(tput setab 5)
export TBX_ANSI_BG_CYAN=$(tput setab 6)
export TBX_ANSI_BG_WHITE=$(tput setab 7)
export TBX_ANSI_BG_DEFAULT=$(tput setab 9)
