# Prevent us being sourced multiple times.
if [ ${TOOLBOX_INC_COMMON:-unset} == "unset" ]; then
    echo "Sourcing common.sh"
    export TOOLBOX_INC_COMMON=1
else
    echo "Already sourced: common.sh"
    return
fi

# Dependencies.
. ~/toolbox/etc/.bashrc.d/set_ansi

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

function log()
{
    local level=$1; shift
    local msg=$@

    echo "${level}: ${msg}"
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

at_home && log_info "I am at home"
at_work && log_info "I am at work"
