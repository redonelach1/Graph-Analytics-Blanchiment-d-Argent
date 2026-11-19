"""
Script de génération des images d'emplacement (placeholders) pour le rapport LaTeX.
Crée des visuels professionnels haute résolution dans le dossier report/figures/.
"""

import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)

PLACEHOLDERS = [
    {
        "filename": "fig_placement_layering_integration.png",
        "category": "SCHÉMA MÉTIER AML / TYPOLOGIE",
        "title": "Les Trois Phases Cardinales du Blanchiment de Capitaux",
        "description": "Schéma conceptuel illustrant les étapes de Placement (injection du cash illicite), d'Empilement / Layering (brouillage des pistes par flux complexes) et d'Intégration (réintroduction dans l'économie légale).",
        "target": "Remplacer par un schéma vectoriel ou infographie des flux GAFI."
    },
    {
        "filename": "fig_fanout_fanin_smurfing.png",
        "category": "THÉORIE DES GRAPHES / TYPOLOGIE",
        "title": "Topologie de Schtroumpfage (Smurfing) : Fan-Out & Fan-In",
        "description": "Représentation en graphe orienté de la dispersion fractionnée (1 compte source vers N mules) suivie de la concentration (N mules vers 1 bénéficiaire final).",
        "target": "Remplacer par le graphe exporté de Cytoscape, Gephi ou Directed Canvas Graph."
    },
    {
        "filename": "fig_circular_ring_pattern.png",
        "category": "MOTIF GRAPHFRAMES / TOPOLOGIE",
        "title": "Motif de Boucle Cyclique Fermée (A -> B -> C -> A)",
        "description": "Visualisation du triangle transactionnel avec respect de la fenêtre temporelle Δt <= 7200s, tolérance de conservation de montant (ratio <= 1.15) et calcul des identifiants canoniques.",
        "target": "Remplacer par un schéma de cycle avec montants et horodatages."
    },
    {
        "filename": "fig_lakehouse_architecture.png",
        "category": "ARCHITECTURE SYSTÈME BIG DATA",
        "title": "Architecture Globale Streaming Lakehouse Unifiée",
        "description": "Cartographie complète des flux de données : Ingestion Kafka KRaft -> Spark Structured Streaming -> GraphFrames -> Couches Delta Lake (Bronze/Silver/Gold) -> Next.js 14 Dashboard.",
        "target": "Remplacer par le diagramme d'architecture système officiel."
    },
    {
        "filename": "fig_sliding_window_watermark.png",
        "category": "TRAITEMENT DE FLUX ÉVÉNEMENTIEL",
        "title": "Modélisation Temporelle : Fenêtres Glissantes et Filigrane (Watermark)",
        "description": "Chronogramme illustrant la durée de fenêtre L = 600s, le pas d'avancement S = 30s (20 fenêtres simultanées) et le filigrane W = H - 120s purgeant l'état expiré.",
        "target": "Remplacer par le chronogramme d'exécution temporelle."
    },
    {
        "filename": "fig_fsm_validation_states.png",
        "category": "INGESTION & SÉMANTIQUE",
        "title": "Machine à États Finis (FSM) de Validation et Quarantaine",
        "description": "Diagramme de transition d'états : Événement brut -> Validation de schéma -> Filtrage d'horodatage futur -> Déduplication SHA-256 -> Routage Silver ou Quarantaine.",
        "target": "Remplacer par le diagramme d'états FSM de validation."
    },
    {
        "filename": "fig_screenshot_spark_ui.png",
        "category": "CAPTURE D'ÉCRAN / RUNTIME DISTRIBUÉ",
        "title": "Console Apache Spark 3.5.0 : Plan d'Exécution et DAG Streaming",
        "description": "Capture d'écran de l'interface Spark Web UI (port 8080/4040) montrant le DAG des micro-lots, les statistiques de shuffling et la latence de traitement des jointures GraphFrames.",
        "target": "Insérer une capture d'écran réelle de l'interface Spark Master / Jobs UI."
    },
    {
        "filename": "fig_screenshot_kafka_console.png",
        "category": "CAPTURE D'ÉCRAN / MESSAGING",
        "title": "Interface Apache Kafka UI : Topics et Télémétrie des Flux",
        "description": "Capture d'écran du tableau de bord Kafka UI (port 8090) visualisant les messages du topic financial-transactions et l'émission en temps réel des fraud-alerts.",
        "target": "Insérer une capture d'écran de la console Kafka UI."
    },
    {
        "filename": "fig_screenshot_dashboard_overview.png",
        "category": "CAPTURE D'ÉCRAN / COCKPIT FORENSIQUE",
        "title": "Cockpit Next.js 14 : Vue Exécutive et Indicateurs Clés (KPIs)",
        "description": "Capture d'écran du tableau de bord AML compliance : Cartes métriques (Volumes, Taux de détection, Débit instantané), jauge de risque global et indicateurs d'état du streaming.",
        "target": "Insérer une capture de la page d'accueil du dashboard (http://localhost:3000)."
    },
    {
        "filename": "fig_screenshot_dashboard_graph.png",
        "category": "CAPTURE D'ÉCRAN / COCKPIT FORENSIQUE",
        "title": "Cockpit Next.js 14 : Rendu Vectoriel du Graphe Circulaire de Fraude",
        "description": "Capture d'écran de la composante Directed Canvas Graph montrant les nœuds comptes bancaires (badges de risque rouge/ambre), les arêtes animées et l'inspecteur de transaction.",
        "target": "Insérer une capture de la vue d'investigation de cycle avec topologie interactive."
    },
    {
        "filename": "fig_screenshot_dashboard_cycles.png",
        "category": "CAPTURE D'ÉCRAN / COCKPIT FORENSIQUE",
        "title": "Cockpit Next.js 14 : Registre Médico-Légal des Cycles et Alertes Détectées",
        "description": "Capture d'écran du tableau récapitulatif des alertes dans le cockpit shadcn/ui : Cycle ID, sévérité, durée du cycle, montant cumulé, comptes impliqués et horodatage.",
        "target": "Insérer une capture du tableau des alertes et cycles frauduleux."
    },
    {
        "filename": "fig_screenshot_dashboard_sar.png",
        "category": "CAPTURE D'ÉCRAN / EXPORT RÉGLEMENTAIRE",
        "title": "Cockpit Next.js 14 : Générateur et Exportateur de Dossier SAR (JSON)",
        "description": "Capture d'écran du tiroir ou de la boîte de dialogue d'export réglementaire SAR (Suspicious Activity Report) affichant la charge utile médico-légale normalisée.",
        "target": "Insérer une capture du panneau d'export SAR au format JSON conforme."
    },
    {
        "filename": "fig_screenshot_dashboard_pagerank.png",
        "category": "CAPTURE D'ÉCRAN / ANALYSE SPECTRALE",
        "title": "Cockpit Next.js 14 : Télémétrie PageRank et Carrefours Marchands",
        "description": "Capture d'écran visualisant les comptes à fort score de centralité PageRank, les composantes connexes et la démonstration de séparation des marchands légitimes (AT-17).",
        "target": "Insérer une capture de la section d'analyse spectrale PageRank."
    },
    {
        "filename": "fig_benchmark_throughput_latency.png",
        "category": "BENCHMARKING EXPÉRIMENTAL / PERFORMANCE",
        "title": "Courbes de Performance : Débit de Traitement vs. Latence au 95e Centile",
        "description": "Graphique comparatif des 3 paliers d'évaluation : L1 (10 TPS - 0.43 ms), L2 (100 TPS - 1.47 ms) et L3 (500 TPS - 18.95 ms) prouvant l'absence de saturation.",
        "target": "Insérer le graphique de benchmarking généré par scripts/run_benchmarks.py."
    },
    {
        "filename": "fig_pagerank_distribution.png",
        "category": "ANALYSE SPECTRALE / VALIDATION",
        "title": "Distribution Spectrale du PageRank et Isolation des Carrefours Marchands",
        "description": "Histogramme de distribution comparant le score des nœuds marchands légitimes (in-degree élevé) face aux comptes mules des boucles criminelles (conservation fermée).",
        "target": "Insérer la visualisation de distribution des scores de centralité."
    }
]

def create_placeholder(data):
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), color=(248, 250, 252)) # Slate 50
    draw = ImageDraw.Draw(img)

    # 1. Subtle background blueprint grid
    grid_color = (226, 232, 240) # Slate 200
    for x in range(0, width, 40):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, 40):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)

    # 2. Main technical frame with rounded corners
    margin = 50
    frame_box = [margin, margin, width - margin, height - margin]
    draw.rectangle(frame_box, outline=(148, 163, 184), width=3) # Slate 400

    # Inner decorative dashed-look corner brackets
    bracket_len = 30
    b_color = (15, 23, 42) # Slate 900
    # Top-Left
    draw.line([(margin + 10, margin + 10), (margin + 10 + bracket_len, margin + 10)], fill=b_color, width=3)
    draw.line([(margin + 10, margin + 10), (margin + 10, margin + 10 + bracket_len)], fill=b_color, width=3)
    # Top-Right
    draw.line([(width - margin - 10, margin + 10), (width - margin - 10 - bracket_len, margin + 10)], fill=b_color, width=3)
    draw.line([(width - margin - 10, margin + 10), (width - margin - 10, margin + 10 + bracket_len)], fill=b_color, width=3)
    # Bottom-Left
    draw.line([(margin + 10, height - margin - 10), (margin + 10 + bracket_len, height - margin - 10)], fill=b_color, width=3)
    draw.line([(margin + 10, height - margin - 10), (margin + 10, height - margin - 10 - bracket_len)], fill=b_color, width=3)
    # Bottom-Right
    draw.line([(width - margin - 10, height - margin - 10), (width - margin - 10 - bracket_len, height - margin - 10)], fill=b_color, width=3)
    draw.line([(width - margin - 10, height - margin - 10), (width - margin - 10, height - margin - 10 - bracket_len)], fill=b_color, width=3)

    # 3. Header badge
    badge_w, badge_h = 550, 48
    bx = (width - badge_w) // 2
    by = margin + 35
    draw.rectangle([bx, by, bx + badge_w, by + badge_h], fill=(15, 23, 42)) # Slate 900

    # Fonts: PIL default font (handles text anywhere)
    try:
        font_badge = ImageFont.truetype("arial.ttf", 20)
        font_title = ImageFont.truetype("arialbd.ttf", 36)
        font_body = ImageFont.truetype("arial.ttf", 22)
        font_target = ImageFont.truetype("arialbd.ttf", 22)
        font_meta = ImageFont.truetype("ariali.ttf", 18)
    except Exception:
        font_badge = font_title = font_body = font_target = font_meta = ImageFont.load_default()

    # Draw badge text
    draw.text((bx + badge_w // 2, by + 12), data["category"], fill=(241, 245, 249), anchor="mt", font=font_badge)

    # 4. Central Icon Symbol (Camera / Document / Graph)
    icon_cy = height // 2 - 110
    draw.ellipse([width // 2 - 45, icon_cy - 45, width // 2 + 45, icon_cy + 45], outline=(30, 41, 59), width=4)
    draw.ellipse([width // 2 - 25, icon_cy - 25, width // 2 + 25, icon_cy + 25], fill=(30, 41, 59))
    draw.rectangle([width // 2 - 70, icon_cy - 35, width // 2 + 70, icon_cy + 35], outline=(30, 41, 59), width=3)

    # 5. Figure Title
    draw.text((width // 2, height // 2 - 15), data["title"], fill=(15, 23, 42), anchor="mt", font=font_title)

    # 6. Description (word wrapped)
    desc = data["description"]
    # Simple wrap
    words = desc.split()
    lines = []
    cur_line = []
    for w in words:
        cur_line.append(w)
        if len(" ".join(cur_line)) > 90:
            lines.append(" ".join(cur_line))
            cur_line = []
    if cur_line:
        lines.append(" ".join(cur_line))

    desc_y = height // 2 + 50
    for line in lines:
        draw.text((width // 2, desc_y), line, fill=(51, 65, 85), anchor="mt", font=font_body)
        desc_y += 32

    # 7. Action box (Replacement Instructions)
    action_w, action_h = 1100, 110
    ax = (width - action_w) // 2
    ay = height - margin - 150
    draw.rectangle([ax, ay, ax + action_w, ay + action_h], fill=(238, 242, 255), outline=(99, 102, 241), width=2) # Indigo tint

    draw.text((ax + action_w // 2, ay + 18), "📌 EMPLACEMENT RÉSERVÉ — INSÉRER LA CAPTURE D'ÉCRAN OU VISUEL", fill=(67, 56, 202), anchor="mt", font=font_target)
    draw.text((ax + action_w // 2, ay + 50), f"Fichier cible : report/figures/{data['filename']} (Résolution conseillée : 1920 x 1080 px)", fill=(30, 41, 59), anchor="mt", font=font_body)
    draw.text((ax + action_w // 2, ay + 80), data["target"], fill=(71, 85, 105), anchor="mt", font=font_meta)

    # Save to disk
    out_path = os.path.join(OUTPUT_DIR, data["filename"])
    img.save(out_path, format="PNG", dpi=(300, 300))
    print(f"Généré : {data['filename']}")

if __name__ == "__main__":
    print(f"Génération de {len(PLACEHOLDERS)} images d'emplacement dans {OUTPUT_DIR}...")
    for item in PLACEHOLDERS:
        create_placeholder(item)
    print("Génération terminée avec succès !")
