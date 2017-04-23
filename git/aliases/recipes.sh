#!/usr/local/bin/bash

cat <<EOF
After cbgit wg checkout <workgroup>, master is sometimes ahead of origin because some rebasing happened and
commits from personal-fork got merged in master. If you are sure that all the commits in personal-fork can
be discarded:
* git log1 --decorate # to find XXX, the commit origin is on
* git reset --hard XXX
* git push --force personal-fork
EOF
