.PHONY: algorithm.pdf all clean

all: algorithm.pdf

algorithm.pdf: algorithm.tex algorithm.bib algorithm.sketch
	sketchtool export artboards algorithm.sketch
	latexmk -pdf -pdflatex="pdflatex -interaction=nonstopmode" -use-make algorithm.tex

clean:
	latexmk -CA
