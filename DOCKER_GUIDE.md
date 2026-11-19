# 🐳 Guide d'Exécution de la Pile Docker Compose
## Plateforme Big Data de Détection en Temps Réel du Blanchiment d'Argent par Analyse de Graphes
### ENSAM Rabat — Projet Académique Big Data 2026/2027

---

## 1. Vue d'Ensemble des Services et Points d'Accès

La pile Docker Compose (`docker-compose.yml`) orchestre **l'intégralité des 4 livrables ingénieur** et fournit une infrastructure conteneurisée reproductible :

| Conteneur | Service Compose | Port Hôte | Interface Web / Rôle | Accès Direct |
| :--- | :--- | :---: | :--- | :---: |
| **`aml-kafka`** | `kafka` | `9092`, `9094` | Broker Apache Kafka 3.5.1 en mode KRaft (sans ZooKeeper) | Client Kafka TCP |
| **`aml-kafka-init`** | `kafka-init` | *(interne)* | Initialisation automatique des topics (`financial-transactions`, `fraud-alerts`) | One-shot |
| **`aml-kafka-ui`** | `kafka-ui` | `8090` | Console Web d'inspection des topics, offsets et partitions | [http://localhost:8090](http://localhost:8090) |
| **`aml-spark-master`** | `spark-master` | `8080`, `7077` | Console Web du Cluster Master Apache Spark 3.5.1 | [http://localhost:8080](http://localhost:8080) |
| **`aml-spark-worker`** | `spark-worker` | `8081` | Nœud exécuteur Spark alloué à 4 cœurs CPU et 4 Go de mémoire RAM | Interne |
| **`aml-spark-app`** | `spark-app` | `4040` | **Livrables 2 & 3 :** Moteur Spark Structured Streaming, GraphFrames & Delta Lake | [http://localhost:4040](http://localhost:4040) |
| **`aml-producer`** | `producer` | *(interne)* | **Livrable 1 :** Producteur de flux financier continu avec injection de boucles de fraude | CLI Background |
| **`aml-dashboard`** | `dashboard` | `3000` | Cockpit Web de Production Next.js 14 (Directed Canvas Graph & Export SAR JSON) | [http://localhost:3000](http://localhost:3000) |
| **`aml-streamlit-dashboard`** | `streamlit-dashboard` | `8501` | **Livrable 4 :** Console interactive Python Streamlit + PyVis (Navigation dans le graphe) | [http://localhost:8501](http://localhost:8501) |

---

## 2. Guide d'Exécution Pas-à-Pas (Commandes Ordonnées)

### Étape 1 : Démarrer l'infrastructure centrale (Kafka & Cluster Spark)
Cette commande démarre le bus de messages, initialise les topics et active le cluster Spark :
```bash
docker compose up -d kafka kafka-init kafka-ui spark-master spark-worker
```

**Vérification :**
* Ouvrez **Kafka UI** sur [http://localhost:8090](http://localhost:8090) pour vérifier la création des topics `financial-transactions` et `fraud-alerts`.
* Ouvrez **Spark Master** sur [http://localhost:8080](http://localhost:8080) pour vérifier que le Worker Spark est bien connecté (`ALIVE`, 4 Cores, 4.0 GiB).

---

### Étape 2 : Démarrer le moteur de streaming et les cockpits de supervision
Cette commande active le traitement streaming distribué et les interfaces graphiques :
```bash
docker compose up -d spark-app dashboard streamlit-dashboard
```

**Interfaces opérationnelles immédiatement :**
* **Cockpit Analyste Next.js 14 :** [http://localhost:3000](http://localhost:3000)
  * Vue d'ensemble des KPIs de conformité.
  * Visualisation vectorielle dynamique des cycles $A \to B \to C \to A$ (*Directed Canvas Graph*).
  * Génération et téléchargement en un clic de la Déclaration de Soupçon (*SAR JSON*).
* **Console Interactive Streamlit / PyVis (Livrable 4) :** [http://localhost:8501](http://localhost:8501)
  * Navigation visuelle dans les graphes avec moteur physique interactif.
  * Filtrage par criticité (`CRITICAL`, `HIGH`, `MEDIUM`) et analyse spectrale PageRank.
* **Spark Application Web UI :** [http://localhost:4040](http://localhost:4040)
  * Suivi en temps réel des micro-lots de 5 secondes, débits d'entrée/traitement et DAGs Catalyst.

---

### Étape 3 : Démarrer l'injection de flux transactionnel (Producteur)
Lance l'injection continue de transactions synthétiques avec 10 % de boucles frauduleuses :
```bash
docker compose up -d producer
```

#### Variantes d'injection (à la demande) :
* **Rejouer le jeu de référence IBM AMLSim (20 000 comptes, 200 cycles) :**
  ```bash
  docker compose run --rm producer python src/financial_graph_producer.py --mode amlsim --rate 100
  ```
* **Injection à cadence de stress extrême (500 TPS — Palier L3) :**
  ```bash
  docker compose run --rm producer python src/financial_graph_producer.py --mode mixed --rate 500
  ```
* **Injection d'un cycle triangulaire déterministe immédiat :**
  ```bash
  docker compose run --rm producer python src/financial_graph_producer.py --mode triangle --count 1
  ```

---

## 3. Observation et Inspection en Direct

### A. Consulter les journaux du moteur de streaming Spark
Permet d'observer les fenêtres glissantes de 10 minutes, les micro-lots de 5 secondes et les alertes détectées :
```bash
docker compose logs -f spark-app
```

### B. Consulter les journaux du producteur de transactions
```bash
docker compose logs -f producer
```

### C. Écouter en direct le topic Kafka des alertes de fraude
Affiche en direct les alertes JSON publiées par Spark sur le broker Kafka :
```bash
docker exec -it aml-kafka kafka-console-consumer.sh --bootstrap-server localhost:9094 --topic fraud-alerts --from-beginning
```

### D. Vérifier l'état de santé de tous les conteneurs
```bash
docker compose ps
```

---

## 4. Exécution des Tests et Benchmarks de Performance

Toutes les suites de tests et bancs d'essai s'exécutent directement dans le conteneur `spark-app` :

### A. Validation de la matrice des 22 critères d'acceptation (AT-01 à AT-22)
Exécute la suite complète automatisée sous `pytest` :
```bash
docker exec -it aml-spark-app pytest tests/ -v
```

### B. Campagnes de benchmarks sous charge (Paliers L1, L2, L3)
Mesure les latences P50, P95, les débits effectifs et la consommation mémoire :
```bash
docker exec -it aml-spark-app python scripts/run_benchmarks.py --levels L1,L2,L3
```

### C. Test de fumée rapide (Smoke Test)
Vérifie la disponibilité de Kafka, Delta Lake et GraphFrames :
```bash
docker exec -it aml-spark-app python scripts/smoke_test.py
```

---

## 5. Arrêt et Maintenance de la Pile

* **Mettre en pause les conteneurs sans perte de données :**
  ```bash
  docker compose stop
  ```
* **Relancer les conteneurs en pause :**
  ```bash
  docker compose start
  ```
* **Arrêter et supprimer les conteneurs (en conservant les données des volumes Delta/Kafka) :**
  ```bash
  docker compose down
  ```
* **Réinitialisation complète (suppression des conteneurs ET purge des volumes de données) :**
  ```bash
  docker compose down -v
  ```

---

## 6. Correspondance avec les 4 Livrables Ingénieur

| Fichier Racine | Fichier Source | Rôle Opérationnel | Commande Exécution |
| :--- | :--- | :--- | :--- |
| `financial_graph_producer.py` | `src/financial_graph_producer.py` | Générateur Kafka de transactions & injection de boucles | `python financial_graph_producer.py --mode mixed --rate 20` |
| `spark_graph_fraud_streaming.py` | `src/spark_graph_fraud_streaming.py` | Pipeline streaming Spark, détection GraphFrames & PageRank | `python spark_graph_fraud_streaming.py --role all` |
| `fraud_graph_delta_schema.py` | `src/fraud_graph_delta_schema.py` | Schémas DDL et initialisation des 10 tables Delta Lake | `python fraud_graph_delta_schema.py --init` |
| `graph_network_dashboard.py` | `src/graph_network_dashboard.py` | Interface Streamlit + PyVis de navigation dans les graphes | `streamlit run graph_network_dashboard.py` |
