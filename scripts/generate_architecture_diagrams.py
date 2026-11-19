"""
Génération automatisée des 6 diagrammes conceptuels et d'architecture
pour le rapport académique (report/figures/).
Génère des visuels vectoriels haute résolution (300 DPI) au style publication sobre.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "report", "figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Style global épuré et académique
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 10,
})

# ==============================================================================
# 1. Les trois phases du blanchiment d'argent (Placement, Layering, Integration)
# ==============================================================================
def draw_placement_layering():
    fig, ax = plt.subplots(figsize=(9, 3.8), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")

    stages = [
        {"x": 0.5, "title": "1. PLACEMENT", "sub": "Introduction des fonds", "desc": "• Dépôts d'espèces fractionnés\n• Schtroumpfage (Smurfing)\n• Commerces complices", "color": "#FEF3C7", "border": "#D97706"},
        {"x": 3.7, "title": "2. EMPILEMENT (LAYERING)", "sub": "Brouillage des pistes (Focus Projet)", "desc": "• Multiplication des virements\n• Réseau de comptes mules\n• Boucles cycliques (A → B → C → A)\n• Délais sub-horaires (< 2h)", "color": "#DBEAFE", "border": "#2563EB"},
        {"x": 6.9, "title": "3. INTÉGRATION", "sub": "Réintroduction légale", "desc": "• Achat d'actifs immobiliers\n• Prêts fictifs & dividendes\n• Économie formelle régularisée", "color": "#DCFCE7", "border": "#16A34A"},
    ]

    for s in stages:
        box = patches.FancyBboxPatch((s["x"], 0.4), 2.6, 3.1, boxstyle="round,pad=0.15",
                                     fc=s["color"], ec=s["border"], lw=2)
        ax.add_patch(box)
        ax.text(s["x"] + 1.3, 3.1, s["title"], ha="center", va="center", fontweight="bold", fontsize=11, color="#0F172A")
        ax.text(s["x"] + 1.3, 2.7, s["sub"], ha="center", va="center", style="italic", fontsize=9, color="#475569")
        ax.text(s["x"] + 0.2, 1.5, s["desc"], ha="left", va="center", fontsize=8.5, color="#1E293B", linespacing=1.6)

    # Flèches de transition
    ax.annotate("", xy=(3.6, 2.0), xytext=(3.2, 2.0),
                arrowprops=dict(arrowstyle="->", lw=2.5, color="#0F172A"))
    ax.annotate("", xy=(6.8, 2.0), xytext=(6.4, 2.0),
                arrowprops=dict(arrowstyle="->", lw=2.5, color="#0F172A"))

    plt.title("Cycle Typologique International de Blanchiment des Capitaux (GAFI)", pad=12, fontweight="bold", fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUTPUT_DIR, "fig_placement_layering_integration.png")
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"[OK] {out}")

# ==============================================================================
# 2. Topologie Smurfing : Fan-Out et Fan-In
# ==============================================================================
def draw_fanout_fanin():
    fig, ax = plt.subplots(figsize=(8, 4), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    # Fan-Out (gauche)
    box_left = patches.FancyBboxPatch((0.2, 0.3), 4.4, 4.2, boxstyle="round,pad=0.1", fc="#F8FAFC", ec="#94A3B8", lw=1.2)
    ax.add_patch(box_left)
    ax.text(2.4, 4.15, "Dispersion (Fan-Out)", ha="center", fontweight="bold", fontsize=11, color="#1E293B")
    
    # Centre Source
    src = patches.Circle((0.9, 2.3), 0.35, fc="#EF4444", ec="#991B1B", lw=1.5)
    ax.add_patch(src)
    ax.text(0.9, 2.3, "Src", ha="center", va="center", color="white", fontweight="bold", fontsize=9)

    mules_out = [(3.8, 3.5), (3.8, 2.3), (3.8, 1.1)]
    for i, pt in enumerate(mules_out):
        m = patches.Circle(pt, 0.3, fc="#E2E8F0", ec="#475569", lw=1.5)
        ax.add_patch(m)
        ax.text(pt[0], pt[1], f"M{i+1}", ha="center", va="center", color="#0F172A", fontweight="bold", fontsize=8.5)
        ax.annotate("", xy=(pt[0]-0.35, pt[1]), xytext=(1.3, 2.3),
                    arrowprops=dict(arrowstyle="->", lw=1.5, color="#DC2626"))
        ax.text(2.3, (2.3 + pt[1])/2 + 0.1, "< 10 000 MAD", fontsize=7, color="#64748B", rotation=(pt[1]-2.3)*10)

    # Fan-In (droite)
    box_right = patches.FancyBboxPatch((5.4, 0.3), 4.4, 4.2, boxstyle="round,pad=0.1", fc="#F8FAFC", ec="#94A3B8", lw=1.2)
    ax.add_patch(box_right)
    ax.text(7.6, 4.15, "Concentration (Fan-In)", ha="center", fontweight="bold", fontsize=11, color="#1E293B")

    mules_in = [(6.2, 3.5), (6.2, 2.3), (6.2, 1.1)]
    for i, pt in enumerate(mules_in):
        m = patches.Circle(pt, 0.3, fc="#E2E8F0", ec="#475569", lw=1.5)
        ax.add_patch(m)
        ax.text(pt[0], pt[1], f"M{i+1}", ha="center", va="center", color="#0F172A", fontweight="bold", fontsize=8.5)
        ax.annotate("", xy=(8.7, 2.3), xytext=(pt[0]+0.35, pt[1]),
                    arrowprops=dict(arrowstyle="->", lw=1.5, color="#2563EB"))
        ax.text(7.7, (2.3 + pt[1])/2 + 0.1, "Virement", fontsize=7, color="#64748B", rotation=-(pt[1]-2.3)*10)

    # Destination finale
    dst = patches.Circle((9.1, 2.3), 0.35, fc="#10B981", ec="#065F46", lw=1.5)
    ax.add_patch(dst)
    ax.text(9.1, 2.3, "Dst", ha="center", va="center", color="white", fontweight="bold", fontsize=9)

    plt.title("Topologies Typiques de Schtroumpfage Structuré", pad=12, fontweight="bold", fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUTPUT_DIR, "fig_fanout_fanin_smurfing.png")
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"[OK] {out}")

# ==============================================================================
# 3. Motif Cyclique Fermé A -> B -> C -> A
# ==============================================================================
def draw_circular_ring():
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-2.0, 2.3)
    ax.axis("off")

    # Sommets équilatéraux
    # A (haut), B (bas droit), C (bas gauche)
    A = np.array([0, 1.4])
    B = np.array([1.4, -0.9])
    C = np.array([-1.4, -0.9])

    nodes = [("Compte A\n(Origine)", A, "#DC2626"),
             ("Compte B\n(Mule 1)", B, "#2563EB"),
             ("Compte C\n(Mule 2)", C, "#D97706")]

    # Arêtes orientées
    edges = [
        (A, B, "e1 : 50 000 MAD\nt1 = 10:05", (0.9, 0.45)),
        (B, C, "e2 : 47 500 MAD\nt2 = 10:28", (0.0, -1.35)),
        (C, A, "e3 : 45 000 MAD\nt3 = 11:15", (-0.9, 0.45))
    ]

    for p1, p2, lbl, tpos in edges:
        # Arc légèrement courbé
        ax.annotate("", xy=p2, xytext=p1,
                    arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#0F172A",
                                    connectionstyle="arc3,rad=0.1", mutation_scale=16))
        ax.text(tpos[0], tpos[1], lbl, ha="center", va="center", fontsize=8.5,
                bbox=dict(boxstyle="round,pad=0.3", fc="#F8FAFC", ec="#CBD5E1", lw=0.8),
                fontweight="bold", color="#1E293B")

    # Dessiner les sommets par dessus
    for lbl, pos, col in nodes:
        c = patches.Circle(pos, 0.42, fc=col, ec="#0F172A", lw=2, zorder=5)
        ax.add_patch(c)
        ax.text(pos[0], pos[1], lbl.split('\n')[0], ha="center", va="center",
                color="white", fontweight="bold", fontsize=9, zorder=6)
        # Sous-titre en dehors
        offset = np.array([0, 0.65]) if pos[1] > 0 else np.array([pos[0]*0.3, -0.65])
        ax.text(pos[0] + offset[0], pos[1] + offset[1], lbl.split('\n')[1],
                ha="center", va="center", color="#475569", fontsize=8, style="italic")

    # Encadré critères au centre
    crit = "Critères de Détection :\n• Δt = t3 - t1 ≤ 2 heures\n• Ratio montant ≤ 1.15\n• Conservation capital > 85%"
    ax.text(0, -0.1, crit, ha="center", va="center", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.4", fc="#EFF6FF", ec="#93C5FD", lw=1),
            color="#1E3A8A")

    plt.title("Motif GraphFrames : Boucle Cyclique Fermée (k=3)", pad=14, fontweight="bold", fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUTPUT_DIR, "fig_circular_ring_pattern.png")
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"[OK] {out}")

# ==============================================================================
# 4. Architecture Streaming Lakehouse Medallion
# ==============================================================================
def draw_lakehouse_architecture():
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    # Couches Medallion
    layers = [
        {"x": 0.3, "w": 2.0, "title": "INGESTION", "sub": "Kafka KRaft", "desc": "Topic Transactions\n• 3 partitions\n• Mode Streaming\n• JSON brut", "fc": "#F1F5F9", "ec": "#64748B"},
        {"x": 2.7, "w": 2.1, "title": "BRONZE", "sub": "Raw Delta Lake", "desc": "• Append-only\n• Ingestion brute\n• Horodatage arrivée\n• Rejeu d'audit", "fc": "#FED7AA", "ec": "#EA580C"},
        {"x": 5.2, "w": 2.1, "title": "SILVER", "sub": "Cleansed & Enriched", "desc": "• Validation FSM\n• Hash SHA-256 canonique\n• Quarantaine écartée\n• Fenêtres glissantes", "fc": "#E2E8F0", "ec": "#475569"},
        {"x": 7.7, "w": 2.0, "title": "GOLD", "sub": "Business Alerts", "desc": "• Cycles détectés\n• Métriques PageRank\n• Écritures dédupliquées\n• Export SAR JSON", "fc": "#FEF08A", "ec": "#CA8A04"},
    ]

    for l in layers:
        box = patches.FancyBboxPatch((l["x"], 0.6), l["w"], 3.7, boxstyle="round,pad=0.15",
                                     fc=l["fc"], ec=l["ec"], lw=2)
        ax.add_patch(box)
        ax.text(l["x"] + l["w"]/2, 3.9, l["title"], ha="center", fontweight="bold", fontsize=11, color="#0F172A")
        ax.text(l["x"] + l["w"]/2, 3.5, l["sub"], ha="center", style="italic", fontsize=9, color="#475569")
        ax.text(l["x"] + 0.15, 2.0, l["desc"], ha="left", va="center", fontsize=8.5, color="#1E293B", linespacing=1.6)

    # Flèches de flux entre couches
    for x_arrow in [2.4, 4.9, 7.4]:
        ax.annotate("", xy=(x_arrow + 0.25, 2.4), xytext=(x_arrow - 0.05, 2.4),
                    arrowprops=dict(arrowstyle="->", lw=2.2, color="#0F172A"))

    # Socle Delta Lake ACID sous les tables
    acid_box = patches.FancyBboxPatch((2.7, 0.4), 7.0, 0.45, boxstyle="round,pad=0.08",
                                     fc="#EFF6FF", ec="#3B82F6", lw=1.2)
    ax.add_patch(acid_box)
    ax.text(6.2, 0.62, "Journal de Transactions ACID (_delta_log) & Stockage Parquet Partitionné",
            ha="center", va="center", fontsize=8.5, fontweight="bold", color="#1E40AF")

    plt.title("Architecture Unifiée Streaming Lakehouse Medallion (Delta Lake)", pad=14, fontweight="bold", fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUTPUT_DIR, "fig_lakehouse_architecture.png")
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"[OK] {out}")

# ==============================================================================
# 5. Fenêtrage Glissant & Watermark
# ==============================================================================
def draw_sliding_window_watermark():
    fig, ax = plt.subplots(figsize=(8, 4), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    # Axe temporel
    ax.annotate("", xy=(9.6, 1.0), xytext=(0.4, 1.0),
                arrowprops=dict(arrowstyle="->", lw=2, color="#0F172A"))
    ax.text(9.5, 0.65, "Temps Événementiel (Event Time)", ha="right", fontsize=9, fontweight="bold", color="#0F172A")

    # Fenêtres glissantes
    colors = ["#BFDBFE", "#93C5FD", "#60A5FA"]
    for i in range(3):
        y = 3.6 - i * 0.8
        x_start = 1.0 + i * 1.5
        box = patches.FancyBboxPatch((x_start, y), 4.5, 0.6, boxstyle="round,pad=0.08",
                                     fc=colors[i], ec="#1D4ED8", lw=1.5, alpha=0.9)
        ax.add_patch(box)
        ax.text(x_start + 2.25, y + 0.3, f"Fenêtre {i+1} : Durée L = 10 min (600 s)", ha="center", va="center",
                fontsize=8.5, fontweight="bold", color="#1E3A8A")
        # Flèche de saut
        if i < 2:
            ax.annotate("", xy=(x_start + 1.5, y - 0.2), xytext=(x_start, y - 0.2),
                        arrowprops=dict(arrowstyle="<->", lw=1.2, color="#475569"))
            ax.text(x_start + 0.75, y - 0.4, "Saut = 30 s", ha="center", fontsize=7.5, color="#475569")

    # Ligne de Watermark
    watermark_x = 4.2
    ax.axvline(watermark_x, ymin=0.15, ymax=0.88, color="#DC2626", linestyle="--", lw=2)
    ax.text(watermark_x, 4.65, "Watermark = H - 120 s\n(Seuil de purge mémoire)", ha="center", va="center",
            fontweight="bold", color="#DC2626", fontsize=9)

    # Zone purgée vs zone active
    ax.text(2.2, 0.55, "← Données tardives rejetées\n(Purge de l'état)", ha="center", fontsize=8, color="#DC2626", style="italic")
    ax.text(6.8, 0.55, "Données actives retenues dans le graphe →", ha="center", fontsize=8, color="#16A34A", style="italic")

    plt.title("Gestion de la Mémoire : 20 Fenêtres Imbriquées et Seuil Watermark", pad=14, fontweight="bold", fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUTPUT_DIR, "fig_sliding_window_watermark.png")
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"[OK] {out}")

# ==============================================================================
# 6. Machine à États Finis (FSM) de Validation
# ==============================================================================
def draw_fsm_validation():
    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    # État initial
    p_init = patches.Circle((1.2, 2.5), 0.45, fc="#38BDF8", ec="#0369A1", lw=2)
    ax.add_patch(p_init)
    ax.text(1.2, 2.5, "Événement\nBrut (JSON)", ha="center", va="center", color="white", fontweight="bold", fontsize=8)

    # Décideur Validation
    v_box = patches.FancyBboxPatch((3.2, 1.2), 3.2, 2.6, boxstyle="round,pad=0.15",
                                   fc="#F8FAFC", ec="#334155", lw=2)
    ax.add_patch(v_box)
    ax.text(4.8, 3.45, "Filtres de Validation FSM", ha="center", fontweight="bold", fontsize=10.5, color="#0F172A")
    rules = [
        "1. Schéma 8 champs & Montant > 0",
        "2. Devise admise (MAD)",
        "3. Exclusion auto-virement (src ≠ tgt)",
        "4. Dérive horloge (τ ≤ now + 60s)",
        "5. Conflit Payload SHA-256"
    ]
    for idx, r in enumerate(rules):
        ax.text(3.4, 3.0 - idx*0.38, r, fontsize=8, color="#1E293B")

    # Flèche initial -> validation
    ax.annotate("", xy=(3.15, 2.5), xytext=(1.7, 2.5),
                arrowprops=dict(arrowstyle="->", lw=2, color="#0F172A"))

    # Sortie Succès : SILVER
    p_silver = patches.FancyBboxPatch((7.6, 3.1), 2.1, 1.1, boxstyle="round,pad=0.1",
                                      fc="#DCFCE7", ec="#16A34A", lw=2)
    ax.add_patch(p_silver)
    ax.text(8.65, 3.75, "SILVER STREAM", ha="center", fontweight="bold", color="#166534", fontsize=9.5)
    ax.text(8.65, 3.35, "Injection Graphe\nsilver_transactions", ha="center", fontsize=7.5, color="#14532D")

    # Sortie Échec : QUARANTINE / CONFLICT
    p_quar = patches.FancyBboxPatch((7.6, 0.7), 2.1, 1.1, boxstyle="round,pad=0.1",
                                    fc="#FEE2E2", ec="#DC2626", lw=2)
    ax.add_patch(p_quar)
    ax.text(8.65, 1.35, "QUARANTAINE", ha="center", fontweight="bold", color="#991B1B", fontsize=9.5)
    ax.text(8.65, 0.95, "quarantined_transactions\nconflict_transactions", ha="center", fontsize=7.5, color="#7F1D1D")

    # Flèches de décision
    ax.annotate("", xy=(7.55, 3.65), xytext=(6.45, 3.0),
                arrowprops=dict(arrowstyle="->", lw=2, color="#16A34A"))
    ax.text(6.8, 3.6, "Valide [OK]", fontsize=8, fontweight="bold", color="#16A34A")

    ax.annotate("", xy=(7.55, 1.25), xytext=(6.45, 1.8),
                arrowprops=dict(arrowstyle="->", lw=2, color="#DC2626"))
    ax.text(6.8, 1.4, "Anomalie", fontsize=8, fontweight="bold", color="#DC2626")

    plt.title("Machine à États Finis (FSM) de Contrôle et d'Admission Sémantique", pad=14, fontweight="bold", fontsize=12)
    fig.tight_layout()
    out = os.path.join(OUTPUT_DIR, "fig_fsm_validation_states.png")
    plt.savefig(out, dpi=300)
    plt.close()
    print(f"[OK] {out}")

# ==============================================================================
# Exécution Principale
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("Génération des schémas d'architecture et de concepts mathématiques...")
    print("=" * 70)
    draw_placement_layering()
    draw_fanout_fanin()
    draw_circular_ring()
    draw_lakehouse_architecture()
    draw_sliding_window_watermark()
    draw_fsm_validation()
    print("\n[SUCCÈS] Les 6 diagrammes vectoriels sont générés avec succès !")
