#!/usr/bin/bash

. ~/toolbox/etc/.bashrc.d/common.sh

function usage()
{
    echo <<EOF
Usage: $(basename $0) action

The availabkle actions are:
* symlinks
* git-aliases
EOF
    exit 1
}

function do_symlink()
{
    target=$1
    link=${2:-$(basename ${target})}

    if [ -e ${link} ]; then
	if [ $(readlink -f ${target}) == $(readlink -f ${link}) ]; then
	    log_debug "Skip link ${link} -> ${target} (already up-to-date)"
	else
	    log_warning "Skip link ${link} -> ${target} (already exting but different)"
	fi
	return
    fi
    
    log_info "Create link ${link} -> ${target}"
    ln -s ${target} ${link}
}

function symlinks()
{
    cd ~
    
    do_symlink toolbox/bin
    do_symlink toolbox/git/.gitconfig-global .gitconfig
    do_symlink toolbox/git/.gitignore-global .gitignore

    for x in toolbox/etc/* toolbox/etc/.*; do
	[ -f ${x} ] && do_symlink ${x}
    done
}

function git_aliases()
{
    log_error "Not yet implemented!"
}

case $1 in
    symlinks)
	symlinks
	;;
    git-aliases)
	echo git_aliases
	;;
    *)
	usage
	;;
esac
