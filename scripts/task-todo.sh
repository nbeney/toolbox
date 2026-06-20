#!/usr/bin/bash

if [ $# -eq 0 ]; then
    {
    task tags 2>&1 | grep "^[a-z]" | sed 's/ .*//' | while read TAG; do 
	task +${TAG} custom rc.verbose=0 rc._forcecolor=on
    done
    task -TAGGED custom rc.verbose=0 rc._forcecolor=on
    } | uniq
else
    task $* custom rc.verbose=0 rc._forcecolor=on | uniq
fi
