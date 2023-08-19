# Makefile for Sphinx Documentation

SPHINXOPTS    ?= --jobs auto
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     ?= src
BUILDDIR      ?= build
BUILDVERSION  ?=

.PHONY: help html view Makefile

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

html:
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
	@python ../ci/deploy_docs.py

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
