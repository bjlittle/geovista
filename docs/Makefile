# Minimal makefile for Sphinx documentation
#

export PYVISTA_OFF_SCREEN := True
export PYDEVD_DISABLE_FILE_VALIDATION := 1

# You can set these variables from the command line, and also
# from the environment for the first two.
#
# -W  Warnings promoted to errors
SPHINXOPTS    ?= -W
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = src
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help clean Makefile

clean:
	-rm -rf $(BUILDDIR)
	-rm -rf $(SOURCEDIR)/generated
	-rm -f $(SOURCEDIR)/sg_execution_times.rst

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
