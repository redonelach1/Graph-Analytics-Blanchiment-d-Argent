# 🎓 Rapport de Projet Académique (LaTeX) : AML Graph Analytics

Ce répertoire contient l'intégralité des sources **LaTeX** du rapport de fin d'études / mémoire de projet d'ingénierie Big Data pour le **Mini-Projet 17 : Détection en temps réel du blanchiment d'argent par analyse de graphes distribués**.

---

## 📁 Structure du Projet LaTeX

```text
report/
├── main.tex                       # Document racine maître
├── metadata.tex                   # Titre, auteurs, encadrant, date, institution
├── macros.tex                     # Packages, styles listings, boîtes tcolorbox, \screenshotplaceholder
├── biblio/
│   └── references.bib             # Base de données bibliographique BibTeX (10 citations certifiées)
├── figures/                       # Emplacements réservés et figures (PNG 300 DPI)
│   ├── fig_placement_layering_integration.png
│   ├── fig_fanout_fanin_smurfing.png
│   ├── fig_circular_ring_pattern.png
│   ├── fig_lakehouse_architecture.png
│   ├── fig_sliding_window_watermark.png
│   ├── fig_fsm_validation_states.png
│   ├── fig_screenshot_spark_ui.png
│   ├── fig_screenshot_kafka_console.png
│   ├── fig_screenshot_dashboard_overview.png
│   ├── fig_screenshot_dashboard_graph.png
│   ├── fig_screenshot_dashboard_cycles.png
│   ├── fig_screenshot_dashboard_sar.png
│   ├── fig_screenshot_dashboard_pagerank.png
│   ├── fig_benchmark_throughput_latency.png
│   └── fig_pagerank_distribution.png
├── frontmatter/
│   ├── titlepage.tex              # Page de garde institutionnelle officielle
│   ├── abstract_fr.tex            # Résumé en Français + Mots-clés
│   ├── abstract_en.tex            # Executive Summary en Anglais + Keywords
│   ├── acknowledgements.tex      # Remerciements
│   └── acronyms.tex              # Table des acronymes et définitions
├── chapters/
│   ├── ch1_introduction.tex       # Contexte GAFI, 3 phases du blanchiment, limites SGBDR, objectifs
│   ├── ch2_state_of_art.tex       # Théorie des graphes, Lambda vs Lakehouse, GraphFrames, PageRank
│   ├── ch3_system_architecture.tex# Spécifications, graphe dynamique, math fenêtres/filigrane, tables Delta
│   ├── ch4_streaming_pipeline.tex # Ingestion FSM, SHA-256 canonique, motifs Cypher, scoring risque, AT-17
│   ├── ch5_investigation_dashboard.tex # Cockpit Next.js 14, Directed Canvas Graph, export SAR JSON
│   ├── ch6_experimental_results.tex   # IBM AMLSim 20K, zero leakage, matrice 22 tests d'acceptation, benchmarks
│   └── ch7_conclusion.tex         # Bilan, limites combinatoires k>=5, perspectives T-GNN et cloud
├── appendices/
│   ├── appendix_schemas.tex       # DDL SQL complet des tables Delta Lake
│   ├── appendix_config.tex        # Extrait de configuration YAML (config/default.yaml)
│   └── appendix_tests.tex         # Guide des commandes unifiées de test et benchmark
├── generate_placeholders.py       # Script Python de génération des images d'emplacement
├── compile.bat                    # Script batch de compilation Windows (pdflatex + bibtex)
└── Makefile                       # Makefile Linux / macOS (pdflatex / latexmk)
```

---

## 📷 Insertion de vos Captures d'Écran Personnalisées

Chaque figure et capture d'écran du rapport est gérée via la macro `\screenshotplaceholder` :
1. **Des images d'emplacement (placeholders) haute résolution à 300 DPI ont déjà été générées** dans le dossier `figures/`. Le document compile ainsi immédiatement sans aucune erreur de fichier manquant.
2. Pour remplacer un emplacement par votre propre capture d'écran (ex. une capture réelle de votre cockpit Next.js ou de votre console Kafka) :
   - Prenez votre capture d'écran (résolution conseillée : $1920 \times 1080$ px) ;
   - Nommez le fichier avec le nom attendu (ex. `fig_screenshot_dashboard_overview.png`) ;
   - Déposez-le dans le dossier `report/figures/` en écrasant le placeholder existant ;
   - Recompilez le rapport : votre capture d'écran apparaîtra automatiquement à l'emplacement exact !

---

## 🚀 Compilation Locale

### Option 1 : Via le script batch Windows (`compile.bat`)
Double-cliquez sur `compile.bat` ou lancez dans un terminal PowerShell / CMD :
```cmd
cd report
compile.bat
```

### Option 2 : En ligne de commande manuelle (`pdflatex`)
```bash
cd report
pdflatex -synctex=1 -interaction=nonstopmode main.tex
bibtex main
pdflatex -synctex=1 -interaction=nonstopmode main.tex
pdflatex -synctex=1 -interaction=nonstopmode main.tex
```

### Option 3 : Via `latexmk` (recommandé si installé)
```bash
cd report
latexmk -pdf main.tex
```

---

## 🌐 Compilation sur Overleaf (Sans installation locale)

Si vous ne possédez pas de distribution TeX (TeX Live ou MiKTeX) installée localement :
1. Compressez tout le contenu du dossier `report/` dans une archive ZIP (`report.zip`) ;
2. Rendez-vous sur [Overleaf](https://www.overleaf.com) et cliquez sur **New Project** $\to$ **Upload Project** ;
3. Glissez-déposez le fichier `report.zip` ;
4. Dans les paramètres Overleaf (**Menu** en haut à gauche) :
   - **Compiler :** `pdfLaTeX` (ou `XeLaTeX`) ;
   - **TeX Live version :** 2023 ou 2024 ;
   - **Main document :** `main.tex` ;
5. Cliquez sur **Recompile** : le rapport complet de plus de 40 pages est généré instantanément avec figures, tables, extraits de code et bibliographie !
