# Prevent us being sourced multiple times.
if [ ${TOOLBOX_INC_COMMON:-unset} == "unset" ]; then
    echo "Sourcing common.sh"
    export TOOLBOX_INC_COMMON=1
else
    echo "Already sourced: common.sh"
    return
fi

# Dependencies.
. ~/toolbox/etc/.bashrc.d/ansi.sh

#====================================================================
# Logging
#====================================================================

declare -A LOG_LEVEL_TO_COLOR
LOG_LEVEL_TO_COLOR[1]=${ANSI_FG_CYAN}
LOG_LEVEL_TO_COLOR[2]=${ANSI_FG_GREEN}
LOG_LEVEL_TO_COLOR[3]=${ANSI_FG_YELLOW}
LOG_LEVEL_TO_COLOR[4]=${ANSI_FG_RED}

declare -A LOG_LEVEL_TO_NAME
LOG_LEVEL_TO_NAME[1]=DEBUG
LOG_LEVEL_TO_NAME[2]=INFO
LOG_LEVEL_TO_NAME[3]=WARNING
LOG_LEVEL_TO_NAME[4]=ERROR

declare -A LOG_NAME_TO_LEVEL
for level in ${!LOG_LEVEL_TO_NAME[@]}; do
    LOG_NAME_TO_LEVEL[${LOG_LEVEL_TO_NAME[${level}]}]=${level}
done


function log()
{
    local name=$1; shift
    local msg=$@
    
    local level=${LOG_NAME_TO_LEVEL[${name}]}
    local target=${LOG_NAME_TO_LEVEL[${LOG:-INFO}]}
    if [ ${level} -ge ${target} ]; then
	echo "${LOG_LEVEL_TO_COLOR[${level}]}${name}: ${msg}${ANSI_RESET}"
    fi
}

function log_debug()
{
    log DEBUG $@
}

function log_info()
{
    log INFO $@
}

function log_warning()
{
    log WARNING $@
}

function log_error()
{
    log ERROR $@
}

# # Test logging
# for LOG in DEBUG INFO WARNING ERROR; do
#     echo ================= ${LOG}
#     log_debug   "This is a log message at level DEBUG"
#     log_info    "This is a log message at level INFO"
#     log_warning "This is a log message at level WARNING"
#     log_error   "This is a log message at level ERROR"
# done

#====================================================================
# Environment
#====================================================================

function at_home()
{
    hostname | fgrep -iq DESKTOP-2PP2G25
    return $?
}

function at_work()
{
    hostname | fgrep -iq daiwa
    return $?
}

at_home && export TOOLBOX_ENV=home
at_work && export TOOLBOX_ENV=work