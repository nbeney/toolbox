# Prevent us being sourced multiple times.
if [ "${TBX_INC_COMMON}" == "sourced" ]; then
    #echo "Already sourced: common.sh"
    return
else
    #echo "Sourcing common.sh"
    TBX_INC_COMMON="sourced"
fi

# Dependencies.
. ~/toolbox/etc/.bashrc.d/ansi.sh

#====================================================================
# Logging
#====================================================================

declare -A TBX_LOG_LEVEL_TO_COLOR
TBX_LOG_LEVEL_TO_COLOR[1]=${TBX_ANSI_FG_CYAN}
TBX_LOG_LEVEL_TO_COLOR[2]=${TBX_ANSI_FG_GREEN}
TBX_LOG_LEVEL_TO_COLOR[3]=${TBX_ANSI_FG_YELLOW}
TBX_LOG_LEVEL_TO_COLOR[4]=${TBX_ANSI_FG_RED}

declare -A TBX_LOG_LEVEL_TO_NAME
TBX_LOG_LEVEL_TO_NAME[1]=DEBUG
TBX_LOG_LEVEL_TO_NAME[2]=INFO
TBX_LOG_LEVEL_TO_NAME[3]=WARNING
TBX_LOG_LEVEL_TO_NAME[4]=ERROR

declare -A TBX_LOG_NAME_TO_LEVEL
for level in ${!TBX_LOG_LEVEL_TO_NAME[@]}; do
    TBX_LOG_NAME_TO_LEVEL[${TBX_LOG_LEVEL_TO_NAME[${level}]}]=${level}
done


function __tbx_log()
{
    local name=$1; shift
    local msg=$@
    
    local level=${TBX_LOG_NAME_TO_LEVEL[${name}]}
    local target=${TBX_LOG_NAME_TO_LEVEL[${LOG:-INFO}]}
    local color=${TBX_LOG_LEVEL_TO_COLOR[${level}]}
    if [ ${level} -ge ${target} ]; then
	echo "${color}$(basename -- "$0") [${name}] ${msg}${TBX_ANSI_RESET}"
    fi
}

function tbx_log_debug()
{
    __tbx_log DEBUG $@
}

function tbx_log_info()
{
    __tbx_log INFO $@
}

function tbx_log_warning()
{
    __tbx_log WARNING $@
}

function tbx_log_error()
{
    __tbx_log ERROR $@
}

function __tbx_test_logging()
{
    local OLD_LOG=${LOG}
    for LOG in DEBUG INFO WARNING ERROR; do
	echo ================= ${LOG}
	tbx_log_debug   "This is a log message at level DEBUG"
	tbx_log_info    "This is a log message at level INFO"
	tbx_log_warning "This is a log message at level WARNING"
	tbx_log_error   "This is a log message at level ERROR"
    done
    LOG=${OLD_LOG}
}

#====================================================================
# Environment
#====================================================================

function tbx_at_home()
{
    hostname | fgrep -iq DESKTOP-2PP2G25
    return $?
}

function tbx_at_work()
{
    hostname | fgrep -iq daiwa
    return $?
}

tbx_at_home && export TBX_ENV=home
tbx_at_work && export TBX_ENV=work
