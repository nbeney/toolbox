#!/usr/local/bin/bash

git stash list | cut -d: -f1 | while read x; do 
    echo ================== $x 
    git stash show $x
done
