#!/usr/local/bin/bash

TMP_FILE=/tmp/$(basename $0).$$

find . -name .git | while read GIT_DIR; do 
    PARENT_DIR=$(echo ${GIT_DIR} | sed "s|/.git$||")

    (
        cd ${PARENT_DIR}
        git status
        git stash list
    ) \
        | egrep -v '^no changes added to commit \(use "git add" and/or "git commit -a"\)$' \
        | egrep -v '^nothing added to commit but untracked files present \(use "git add" to track\)$' \
        | egrep -v "^nothing to commit, working directory clean$" \
        | egrep -v "^On branch develop$" \
        | egrep -v "^On branch master$" \
        | egrep -v "^Your branch is up-to-date with 'origin/develop'.$" \
        | egrep -v "^Your branch is up-to-date with 'origin/develop'.$" \
        | egrep -v "^Your branch is up-to-date with 'origin/master'.$" \
        | egrep -v '^  \(use "git add <file>..." to include in what will be committed\)$' \
        | egrep -v '^  \(use "git add <file>..." to mark resolution\)$' \
        | egrep -v '^  \(use "git add <file>..." to update what will be committed\)$' \
        | egrep -v '^  \(use "git checkout -- <file>..." to discard changes in working directory\)$' \
        | egrep -v '^  \(use "git push" to publish your local commits\)$' \
        > ${TMP_FILE}
    
    if [ -s ${TMP_FILE} ]; then
        echo ================== ${PARENT_DIR}
        cat ${TMP_FILE}
    fi
done

rm -f ${TMP_FILE}
