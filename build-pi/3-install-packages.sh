#!/bin/bash

function run()
{
    PACKAGE=$1
    echo ======================================================================
    echo ${PACKAGE}
    echo ======================================================================
    echo sudo apt-get install ${PACKAGE}
}

run attr
run dnsutils
run emacs24-nox
run htop
run lsof
run nmap
run pdns-server pdns-recursor
run samba
run samba-common
run samba-common-bin
run silversearcher-ag
run telnet
run tightvncserver
run tmux
