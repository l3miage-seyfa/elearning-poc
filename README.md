# POC — Système de E-Learning basé sur l'IA Générative

> **Cours** : Systèmes de Gestion des Connaissances (SGC) — M2 MIAGE  
> **Type** : Proof of Concept  
> **Soutenance** : Mai / Juin 2026

---

## Démarrage rapide

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # puis renseigner OPENAI_API_KEY
python manage.py migrate
python manage.py runserver
```

Ouvrir : **http://127.0.0.1:8000**  
Compte admin : `admin@poc.com` / `admin1234`

---

## Documentation

| Fichier | Contenu |
|---------|---------|
| [docs/ROADMAP.md](docs/ROADMAP.md) | Avancement des phases (✅ / 🔄 / 🔲) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Structure du code, modèles, URLs, flux |
| [docs/SERVICES.md](docs/SERVICES.md) | Couche `services/` : IA, stockage, décorateurs |
| [docs/PROGRESS.md](docs/PROGRESS.md) | Journal de développement et décisions techniques |
| [PROJET.md](PROJET.md) | Spécification fonctionnelle complète |
| [Technologie.md](Technologie.md) | Analyse des outils e-learning existants |

---

## Stack

```
Backend     : Python 3.13 + Django 5.2
LLM         : OpenAI GPT-4o
PDF parsing : PyMuPDF
Stockage    : Railway Storage Bucket (S3-compatible)
Base locale : SQLite  |  Base prod : Railway PostgreSQL
Frontend    : Bootstrap 5.3 + Bootstrap Icons
Déploiement : Railway (auto-deploy GitHub)
```

---

## Structure du projet

```
.
├── README.md
├── PROJET.md               # Spec fonctionnelle
├── Technologie.md          # Analyse outils existants
├── Cours.md                # Consignes du cours SGC
├── docs/
│   ├── ROADMAP.md          # Avancement phases
│   ├── ARCHITECTURE.md     # Architecture technique
│   ├── SERVICES.md         # Documentation services/
│   └── PROGRESS.md         # Journal de dev
├── backend/                # Application Django
│   ├── accounts/
│   ├── groups/
│   ├── courses/
│   ├── participations/
│   ├── services/
│   └── templates/
├── data/                   # Jeux de données (anonymisés)
└── frontend/               # (réservé)
```

---

## Avancement

| Phase | Description | Statut |
|-------|-------------|--------|
| 0 | Prérequis comptes & outils | ✅ |
| 1 | Setup Django & architecture modulaire | ✅ |
| 2 | Upload PDF + génération IA (slides + quiz) | ✅ |
| 3 | CRUD web Personnes & Groupes | 🔲 |
| 4 | Interface responsable de groupe | 🔲 |
| 5 | Review & édition avant publication | 🔲 |
| 6 | Flow participation amélioré | 🔲 |
| 7 | Déploiement Railway | 🔲 |
| 8 | [BONUS] Chatbot RAG | 🔲 |
| 9 | Bilan & soutenance | 🔲 |

