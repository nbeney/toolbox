help:
	@echo "symlinks"

files := $(wildcard ~/toolbox/etc/*)

.ONESHELL:
symlinks:
	@cd 
	@ln -s ~/toolbox/bin
	@ln -s ~/toolbox/git/.git-completion.bash
	@ln -s ~/toolbox/git/.gitconfig-global .gitconfig
	@ln -s ~/toolbox/git/.gitignore-global .gitignore

	@for x in $(files); do \
	    ln -s $${x}; \
	done

aliases := $(wildcard ~/toolbox/git/aliases/*)

git-aliases:
	@{ \
	    echo "[alias]"; \
	    for x in ${aliases}; do \
	        echo "    $$(basename $${x} | cut -d. -f1) = ! $${x}"; \
	    done; \ 
	} >> xxx
