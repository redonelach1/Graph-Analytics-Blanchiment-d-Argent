# Makefile pour la compilation du rapport LaTeX

MAIN = main
PDFLATEX = pdflatex -synctex=1 -interaction=nonstopmode
BIBTEX = bibtex

.PHONY: all clean cleanall

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex biblio/references.bib
	$(PDFLATEX) $(MAIN).tex
	$(BIBTEX) $(MAIN)
	$(PDFLATEX) $(MAIN).tex
	$(PDFLATEX) $(MAIN).tex

clean:
	rm -f *.aux *.log *.out *.toc *.lof *.lot *.lol *.bbl *.blg *.synctex.gz
	rm -f frontmatter/*.aux chapters/*.aux appendices/*.aux

cleanall: clean
	rm -f $(MAIN).pdf
