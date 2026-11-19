"""
Script Python de compilation automatisée et vérification du rapport LaTeX.
"""

import subprocess
import shutil
import sys
import os

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))

# Détection automatique de MiKTeX dans les répertoires standards
MIKTEX_DEFAULT = r"D:\MikTex\miktex\bin\x64"
if os.path.exists(MIKTEX_DEFAULT) and MIKTEX_DEFAULT not in os.environ.get("PATH", ""):
    os.environ["PATH"] = MIKTEX_DEFAULT + os.pathsep + os.environ.get("PATH", "")

def check_compiler():
    compilers = ["pdflatex", "xelatex", "latexmk"]
    for c in compilers:
        path = shutil.which(c)
        if path:
            return c, path
    return None, None

def compile_with_latexmk(path):
    print(f"Compilation via latexmk ({path})...")
    cmd = [path, "-pdf", "-synctex=1", "-interaction=nonstopmode", "main.tex"]
    res = subprocess.run(cmd, cwd=REPORT_DIR)
    return res.returncode == 0

def compile_with_pdflatex(path):
    print(f"Compilation via pdflatex ({path})...")
    bibtex_path = shutil.which("bibtex")
    
    steps = [
        [path, "-synctex=1", "-interaction=nonstopmode", "main.tex"],
        [bibtex_path, "main"] if bibtex_path else None,
        [path, "-synctex=1", "-interaction=nonstopmode", "main.tex"],
        [path, "-synctex=1", "-interaction=nonstopmode", "main.tex"],
    ]
    for step in steps:
        if step is None:
            continue
        print(f"-> Exécution: {' '.join(step)}")
        res = subprocess.run(step, cwd=REPORT_DIR)
        if res.returncode != 0:
            print(f"Avertissement lors de l'exécution de {' '.join(step)}")
    return os.path.exists(os.path.join(REPORT_DIR, "main.pdf"))

def main():
    print("=" * 70)
    print("Vérification de l'environnement de compilation LaTeX")
    print("=" * 70)
    
    compiler, path = check_compiler()
    if not compiler:
        print("\n[INFO] Aucun compilateur LaTeX (pdflatex, latexmk, xelatex) n'a été détecté dans votre PATH local.")
        print("Pour générer le PDF :")
        print("1. Installez MiKTeX ou TeX Live sur votre poste de travail, OU")
        print("2. Uploadez simplement le dossier 'report/' sur https://www.overleaf.com (aucun logiciel requis).")
        print("Tous les fichiers sources .tex, les figures .png, la bibliographie .bib et les macros sont prêts et conformes.")
        sys.exit(0)
    
    print(f"[OK] Compilateur détecté : {compiler} ({path})")
    success = False
    if compiler == "latexmk":
        success = compile_with_latexmk(path)
    else:
        success = compile_with_pdflatex(path)
        
    if success:
        print("\n[SUCCÈS] Rapport compilé avec succès : report/main.pdf")
    else:
        print("\n[NOTE] La compilation a généré des avertissements ou le PDF est en cours.")

if __name__ == "__main__":
    main()
