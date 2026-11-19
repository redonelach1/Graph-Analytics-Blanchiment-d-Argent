@echo off
echo ==============================================================================
echo  Compilation du Rapport Academique LaTeX : AML Graph Analytics (Mini-Projet 17)
echo ==============================================================================

if exist "D:\MikTex\miktex\bin\x64" (
    set "PATH=D:\MikTex\miktex\bin\x64;%PATH%"
)

where pdflatex >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERREUR] pdflatex n'a pas ete detecte dans votre PATH.
    echo Veuillez installer MiKTeX ou TeX Live, ou importer ce dossier sur Overleaf.
    pause
    exit /b 1
)

echo [1/4] Premiere passe pdflatex...
pdflatex -synctex=1 -interaction=nonstopmode main.tex

echo [2/4] Compilation des references BibTeX...
bibtex main

echo [3/4] Deuxieme passe pdflatex (resolution des citations)...
pdflatex -synctex=1 -interaction=nonstopmode main.tex

echo [4/4] Troisieme passe pdflatex (resolution des renvois et tables)...
pdflatex -synctex=1 -interaction=nonstopmode main.tex

echo ==============================================================================
echo  Compilation terminee avec succes ! Fichier genere : report/main.pdf
echo ==============================================================================
pause
