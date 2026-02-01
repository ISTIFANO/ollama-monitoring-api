# 🚀 Ollama Monitoring API - Projet MLOps

API de monitoring complète pour **Ollama** (modèle **Qwen-8b quantifié**) avec **FastAPI**, **Prometheus**, **Grafana** et **cAdvisor**.  
Architecture optimisée pour **6GB RAM / 2 CPU cores** avec monitoring avancé des ressources.

---

## 📊 Architecture du Projet

```
┌─────────────────────────────────────────────────────────────┐
│                    OLLAMA MONITORING API                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐        │
│  │  Ollama  │◄────►│ FastAPI  │      │ cAdvisor │        │
│  │  qwen2.5 │      │   API    │      │ Metrics  │        │
│  │ (4GB/2CPU)│      │          │      │          │        │
│  └────┬─────┘      └────┬─────┘      └────┬─────┘        │
│       │                 │                  │               │
│       └─────────────────┴──────────────────┘               │
│                         │                                   │
│                  ┌──────▼────────┐                         │
│                  │  Prometheus   │                         │
│                  │  Time-Series  │                         │
│                  │     DB        │                         │
│                  └──────┬────────┘                         │
│                         │                                   │
│                  ┌──────▼────────┐                         │
│                  │    Grafana    │                         │
│                  │  Dashboards   │                         │
│                  └───────────────┘                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Structure Complète du Projet

```
├── docker/                                # Configuration Docker
│   ├── docker-compose.yml                 # Orchestration complète
│   └── monitoring/
│       ├── prometheus.yml                 # Config Prometheus + cAdvisor
│       └── grafana/
│           └── provisioning/
│               ├── datasources/           # Auto-config Prometheus
│               │   └── datasource.yml
│               └── dashboards/            # Dashboards auto-importés
│                   ├── dashboard.yml
│                   └── ollama-dashboard.json
│
├── api/                                   # Application FastAPI
│   ├── Dockerfile                         
│   ├── requirements.txt                   
│   └── app/
│       ├── main.py                        # Point d'entrée + /metrics
│       ├── config.py                      # Config avec optimisations RAM
│       ├── metrics.py                     # Métriques Prometheus custom
│       ├── routers/
│       │   ├── health.py                  # Healthcheck API + Ollama
│       │   └── chat.py                    # Endpoint /chat avec métriques
│       ├── services/
│       │   └── ollama_client.py           # Client HTTP Ollama
│       └── utils/
│           ├── retry.py                   # Retry logic avec backoff
│           └── timers.py                  # Mesure latence précise
│
├── scripts/                               # Scripts DevOps
│   ├── setup_model.py                     # Installation modèle optimisé
│   ├── stress_test.py                     # Test de charge
│   └── warmup.py                          # Pré-chargement modèle
│
├── .env                                   # Variables d'environnement
├── README.md                              # Cette documentation
└── Makefile                               # Commandes pratiques
```

---

## 🎯 Fonctionnalités MLOps

### ✅ Monitoring Complet
- **RAM Usage** : Suivi en temps réel de la consommation mémoire du container Ollama
- **CPU Usage** : Monitoring de l'utilisation CPU avec alertes de seuil
- **OOM Events** : Détection des événements Out-Of-Memory
- **Latence API** : Mesure des temps de réponse (p50, p95, p99)
- **Request Rate** : Taux de requêtes (succès vs erreurs)
- **Network I/O** : Bande passante réseau du container

### 🔧 Optimisations pour 4GB RAM
- Limites strictes Docker: `mem_limit: 4G`, `cpus: 2.0`
- Modèle quantifié recommandé: `qwen2.5:0.5b` (500MB)
- Variables d'environnement optimisées:
  - `OLLAMA_NUM_PARALLEL=1` : Un seul modèle en mémoire
  - `OLLAMA_MAX_LOADED_MODELS=1` : Évite le multi-modèle
  - `OLLAMA_FLASH_ATTENTION=1` : Optimisation mémoire attention

### 📡 Exposition des Métriques
- **FastAPI** `/metrics` : Métriques applicatives (requests, latency, errors)
- **cAdvisor** `:8080/metrics` : Métriques containers (RAM, CPU, I/O, OOM)
- **Prometheus** `:9090` : Agrégation et stockage time-series
- **Grafana** `:3000` : Dashboards visuels (login: admin/admin)

---

## 🚀 Démarrage Rapide

### Prérequis
- Docker & Docker Compose
- **10GB RAM minimum** sur la machine hôte (6GB pour Ollama + overhead)
- Python 3.11+ (pour scripts hors Docker)

### Étape 1 : Démarrer les Services

```bash
# Construire et démarrer tous les containers
make up

# Alternative sans Makefile
cd docker
docker-compose up -d
```

**Services disponibles :**
- API FastAPI : http://localhost:8000
- Documentation API : http://localhost:8000/docs
- cAdvisor : http://localhost:8080
- Prometheus : http://localhost:9090
- Grafana : http://localhost:3000 (admin/admin)

### Étape 2 : Installer le Modèle Qwen-8b

```bash
# Attendre que le container Ollama soit démarré (30-40 secondes)
docker-compose logs -f ollama

# Installer le modèle qwen-8b quantifié (recommandé)
python scripts/setup_model.py
```

**Options de modèles pour 6GB RAM (qwen-8b quantifiés) :**
| Modèle | Taille | Quantization | Description |
|--------|--------|--------------|-------------|
| `qwen2.5:7b-instruct-q4_0` | 4.4GB | q4_0 | ✅ **Recommandé** - Bon équilibre |
| `qwen2.5:7b-instruct-q4_K_M` | 4.7GB | q4_K_M | ✅ Meilleure qualité |
| `qwen2.5:7b-instruct-q5_K_M` | 5.4GB | q5_K_M | ✅ Qualité maximale |

> **Note:** qwen2.5:7b-instruct correspond au modèle qwen-8b avec différents niveaux de quantization.

### Étape 3 : Vérifier le Monitoring

```bash
# Tester l'API
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum computing in one sentence"}'

# Accéder au dashboard Grafana
open http://localhost:3000
# Login: admin / admin
# Dashboard: "Ollama Monitoring - MLOps Dashboard"
```

---

## 📊 Dashboard Grafana

Le dashboard inclut automatiquement :

### 📈 Panels Disponibles
1. **Memory Usage** - Consommation RAM vs limite 4GB
2. **CPU Usage** - Utilisation CPU en pourcentage
3. **OOM Events** - Compteur d'événements Out-Of-Memory
4. **Memory Usage %** - Gauge RAM en %
5. **Total Requests** - Nombre total de requêtes API
6. **API Latency (p95)** - Latence 95ème percentile
7. **API Response Time** - Temps de réponse p50/p95/p99
8. **Request Rate** - Taux de requêtes succès vs erreurs
9. **Network I/O** - Bande passante réseau

### 🎨 Visualisation
- Refresh automatique toutes les 10 secondes
- Période par défaut : 1 heure
- Tags : `ollama`, `monitoring`, `mlops`

---

## 🔍 Métriques Prometheus Disponibles

### Métriques cAdvisor (Container)
```promql
# Utilisation mémoire
container_memory_usage_bytes{name="ollama"}

# Limite mémoire
container_spec_memory_limit_bytes{name="ollama"}

# Utilisation CPU
rate(container_cpu_usage_seconds_total{name="ollama"}[1m])

# Événements OOM
container_oom_events_total{name="ollama"}

# Réseau I/O
rate(container_network_receive_bytes_total{name="ollama"}[1m])
rate(container_network_transmit_bytes_total{name="ollama"}[1m])
```

### Métriques FastAPI Custom
```promql
# Requêtes totales
ollama_requests_total{method="POST", endpoint="/chat", status="success"}

# Latence (histogram)
histogram_quantile(0.95, rate(ollama_request_duration_seconds_bucket[5m]))

# Requêtes actives
ollama_active_requests

# Erreurs
ollama_errors_total{error_type="TimeoutError"}
```

---

## 🛠️ Commandes Utiles (Makefile)

```bash
make help       # Afficher toutes les commandes disponibles
make build      # Construire les containers
make up         # Démarrer tous les services
make down       # Arrêter tous les services
make logs       # Suivre les logs en temps réel
make restart    # Redémarrer les services
make clean      # Nettoyer complètement (volumes + images)
make stress     # Lancer un test de charge
make warmup     # Préchauffer le modèle
```

---

## 💡 Conseils d'Optimisation Mémoire
Configuration Optimale pour qwen-8b (6GB RAM)

#### 1. Modèle Recommandé
```bash
# ✅ Recommandé pour 6GB - qwen-8b quantifié
qwen2.5:7b-instruct-q4_0   # 4.4GB - Meilleur équilibre
qwen2.5:7b-instruct-q4_K_M # 4.7GB - Qualité supérieure
qwen2.5:7b-instruct-q5_K_M # 5.4GB - Qualité maximale
```

#### 2. Variables d'environnement Docker
```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 6G      # 6GB pour qwen-8b
    reservations:
      memory: 3G
      
environment:
  - OLLAMA_NUM_PARALLEL=1        # Limite à 1 modèle simultané
  - OLLAMA_MAX_LOADED_MODELS=1   # Pas de multi-modèle
  - OLLAMA_FLASH_ATTENTION=1     # Optimise l'attention mechanism
```

#### 3. Configuration API
```python
# config.py
MAX_CONTEXT_LENGTH=4096  # Contexte adapté pour qwen-8b
ENABLE_STREAMING=true    # Streaming disponible avec 6GB
ENABLE_STREAMING=false   # Désactive streaming (réduit charge)
```

#### 4. Rate Limiting
```bash
# Limiter les requêtes concurrentes
MAX_REQUESTS_PER_MINUTE=60
```

### 📉 Monitoring Proactif

#### Alertes Prometheus (à ajouter)
```yaml
# alerts.yml
- alert: HighMemoryUsage
  expr: (container_memory_usage_bytes{name="ollama"} / container_spec_memory_limit_bytes{name="ollama"}) > 0.9
  for: 2m
  annotations:
    summary: "Ollama utilise >90% de la RAM"

- alert: OOMDetected
  expr: increase(container_oom_events_total{name="ollama"}[5m]) > 0
  annotations:
    summary: "OOM Kill détecté sur Ollama!"
```

### 🔄 Warmup du Modèle

```bash
# Charger le modèle en mémoire avant production
python scripts/warmup.py

# Cela évite la latence du premier appel
```

---

## 🧪 Tests et Validation

### Test de Charge
```bash
# Test avec 50 requêtes, concurrence de 5
python scripts/stress_test.py

# Surveiller Grafana pendant le test pour observer:
# - Pic de CPU
# - Augmentation RAM
# - Latence API
```

### Test Manuel
```bash
# Healthcheck
curl http://localhost:8000/health
curl http://localhost:8000/health/ollama

# Chat simple
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!"}'

# Chat avec modèle spécifique
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain AI", "model": "qwen2.5:0.5b"}'
```

---

## 🔧 Dépannage

### Container Ollama ne démarre pas
```bash
# Vérifier les logs
docker-compose logs ollama

# VérVérifier que vous utilisez bien qwen-8b quantifié
OLLAMA_MODEL=qwen2.5:7b-instruct-q4_0

# 2. Augmenter légèrement la limite si nécessaire
mem_limit: 6G  # Déjà configuré pour qwen-8b

# 3. Surveiller l'utilisation dans Grafana
# Dashboard > Memory Usage devrait rester < 5.5GB5b

# 2. Augmenter la limite (si possible)
mem_limit: 6G

# 3. Réduire le contexte
MAX_CONTEXT_LENGTH=1024
```

### Latence API élevée
```bash
# 1. Préchauffer le modèle
python scripts/warmup.py

# 2. Vérifier l'utilisation CPU/RAM dans Grafana

# 3. Réduire la concurrence
MAX_REQUESTS_PER_MINUTE=30
```

### Grafana dashboard vide
```bash
# Vérifier que Prometheus scrape correctement
curl http://localhost:9090/api/v1/targets

# Vérifier que cAdvisor fonctionne
curl http://localhost:8080/metrics
```

---

## 📚 Ressources Complémentaires

### Documentation Officielle
- [Ollama Documentation](https://github.com/ollama/ollama)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [cAdvisor GitHub](https://github.com/google/cadvisor)

### Modèles Qwen
- [Qwen2.5 Model Card](https://huggingface.co/Qwen)
- Quantization formats: q4_0, q4_K_M, q5_K_M

---

## 🏗️ Architecture MLOps Best Practices

### ✅ Implémenté
- ✅ Séparation des responsabilités (API, Model, Monitoring)
- ✅ Conteneurisation complète avec Docker
- ✅ Observabilité avec métriques Prometheus
- ✅ Dashboards Grafana pour visualisation
- ✅ Healthchecks et retry logic
- ✅ Configuration via variables d'environnement
- ✅ Resource limits (CPU/RAM)
- ✅ Auto-provisioning Grafana

### 🔜 Améliorations Futures
- [ ] Alerting avec Alertmanager
- [ ] CI/CD avec GitHub Actions
- [ ] Tests unitaires et d'intégration
- [ ] Load balancing avec Nginx
- [ ] Logging centralisé (ELK/Loki)
- [ ] Secrets management (Vault)
- [ ] A/B testing de modèles
- [ ] Model versioning

---

## 📝 Configuration Détaillée
7b-instruct-q4_0  # qwen-8b quantifié

# === API Configuration ===
API_TIMEOUT=300                         # Timeout en secondes
MAX_RETRIES=3                           # Nombre de retry
RETRY_DELAY=1                           # Délai entre retries (s)

# === Rate Limiting ===
MAX_REQUESTS_PER_MINUTE=60

# === Memory Optimization (6GB RAM) ===
MAX_CONTEXT_LENGTH=4096                 # Contexte adapté pour qwen-8b
ENABLE_STREAMING=true                   # Streaming disponible avec 6GB
# === Rate Limiting ===
MAX_REQUESTS_PER_MINUTE=60

# === Memory Optimization ===
MAX_CONTEXT_LENGTH=2048              # Limite contexte (tokens)
ENABLE_STREAMING=false               # Désactive streaming
```

### Docker Compose Resources
6G       # 6GB pour qwen-8b
    reservations:
      cpus: '1.0'      # Minimum garanti
      memory: 3
    limits:
      cpus: '2.0'      # Maximum 2 CPU cores
      memory: 4G       # Maximum 4GB RAM
    reservations:
      cpus: '1.0'      # Minimum garanti
      memory: 2G       # RAM minimum garantie
```

---

## 🤝 Contribution

Les contributions sont bienvenues! Pour contribuer:

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📄 Licence

Ce projet est sous licence MIT.

---

## 👤 Auteur

**Ollama Monitoring API** - Projet MLOps/DevOps pour monitoring de modèles LLM

---

## 🎯 Résumé Rapide

```bash
# 1. Démarrer la stack
make up

# 2. Installer le modèle
python scripts/setup_model.py

# 3. Tester l'API
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello world!"}'

# 4. Ouvrir Grafana
open http://localhost:3000  # admin/admin
Ce projet utilise **qwen-8b quantifié en q4** (qwen2.5:7b-instruct-q4_0) avec **6GB de RAM**. Pour des contraintes
# 5. Profit! 🎉
```

---

**Note importante** : Pour utiliser le vrai modèle **qwen-8b en q4**, vous aurez besoin d'au moins **5-6GB de RAM**. Pour rester dans la limite de 4GB, utilisez `qwen2.5:0.5b`, `qwen2.5:1.5b`, ou `qwen2.5:3b`.
