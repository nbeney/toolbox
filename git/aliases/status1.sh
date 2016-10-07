#!/usr/local/bin/bash

CURRENT_BRANCH=$(git branch | grep "^\* " | sed "s/^\* //")

log()
{
    SPEC=$1
    COMMENT=$2

    echo ==================== ${SPEC} ${COMMENT}
    git log1 ${SPEC}
}

echo ==================== status
git status

log "..origin/${CURRENT_BRANCH}" "(missing from local)"
log "origin/${CURRENT_BRANCH}.." "(missing from remote)"
log "..personal-fork/${CURRENT_BRANCH}" "(missing from local)"
log "personal-fork/${CURRENT_BRANCH}.." "(missing from remote)"
