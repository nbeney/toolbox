function at_work()
{
    hostname | fgrep -iq daiwa
    return $?
}
