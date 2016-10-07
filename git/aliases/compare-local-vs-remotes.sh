#!/usr/local/bin/bash

log()
{
    SPEC=$1

    echo ======================================== ${SPEC}
    git log1 ${SPEC}
}

echo ======================================== status
git status

log "..origin/master"
log "origin/master.."
log "..personal-fork/master"
log "personal-fork/master.."
