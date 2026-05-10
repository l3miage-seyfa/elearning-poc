# 📋 PROJET.md — Définition du POC E-Learning IA

## 1. Contexte & Problématique

### Contexte
Dans le cadre du cours **Systèmes de Gestion des Connaissances** (M2 MIAGE), nous devons réaliser un POC basé sur la technologie de **e-learning utilisant une IA générative**.

### Problématique générale
> Comment une équipe ou un service peut-il capitaliser et transmettre ses connaissances internes de façon efficace, personnalisée et automatisée grâce à un LMS augmenté par l'IA ?

---

## 2. Choix à faire (à définir ensemble)

### 2.1 Quel contexte entreprise ?
- [ ] Contexte alternance (à préciser : secteur, équipe, besoins réels)
- [ ] Données disponibles : documents internes, procédures, wikis, PDFs ?

### 2.2 Quelle fonctionnalité principale du POC ?
Choisir **1 ou 2 fonctionnalités** parmi :

| # | Fonctionnalité | Complexité | Impact |
|---|----------------|-----------|--------|
| A | **Génération automatique de quiz** à partir d'un document uploadé | Faible | Fort |
| B | **Résumé / fiche de synthèse** d'un contenu interne via LLM | Faible | Fort |
| C | **Parcours personnalisé** selon le niveau de l'apprenant (adaptatif) | Élevée | Très fort |
| D | **Chatbot pédagogique** qui répond aux questions sur une base de connaissance interne | Moyenne | Très fort |
| E | **Recommandation de modules** selon profil et historique | Élevée | Fort |

### 2.3 Quelle architecture technique ?
| Couche | Options | Recommandation |
|--------|---------|----------------|
| **LLM / IA** | OpenAI GPT-4o, Mistral, Ollama (local) | GPT-4o via API (le plus rapide pour POC) |
| **Backend** | Python FastAPI, Node.js Express | Python FastAPI |
| **Frontend** | Next.js, Streamlit, React | Streamlit (rapidité) ou Next.js (qualité) |
| **Base de données** | PostgreSQL, SQLite, Supabase | SQLite (POC) → Supabase (prod) |
| **Vecteur store (RAG)** | ChromaDB, Pinecone, pgvector | ChromaDB (local, gratuit) |
| **Authentification** | Clerk, Auth.js, simple JWT | Simple JWT pour POC |

### 2.4 Quel pattern IA ?
- [ ] **RAG (Retrieval-Augmented Generation)** : L'IA répond en s'appuyant sur des documents internes → idéal pour chatbot pédagogique et quiz
- [ ] **Prompt Engineering simple** : Envoi direct du texte + instructions au LLM → idéal pour génération de quiz/résumés
- [ ] **Fine-tuning** : Trop lourd pour un POC, à écarter

---

## 3. Proposition de périmètre POC (à valider)

### Scénario proposé : "KnowledgeBoost"
> Une mini-application web qui permet à un collaborateur d'**uploader un document interne** (PDF, Word, texte) et de :
> 1. Obtenir un **résumé structuré** du document
> 2. Générer un **quiz interactif** (5-10 questions QCM) basé sur le contenu
> 3. Voir son **score et les corrections** expliquées par l'IA
> 4. (Bonus) Un **chatbot** pour poser des questions sur le document

Ce scénario couvre :
- ✅ Gestion des connaissances (capitalisation de docs internes)
- ✅ E-learning (apprentissage actif via quiz)
- ✅ IA générative (LLM pour résumé + questions)
- ✅ Faisabilité POC en quelques semaines

---

## 4. Stack technique retenue (à confirmer)

```
Frontend  : Streamlit (Python) ou Next.js 14
Backend   : Python + FastAPI
IA        : OpenAI GPT-4o (API) ou Mistral via Ollama
RAG       : LangChain + ChromaDB
BDD       : SQLite (POC)
Déploiement : Local / Docker
```

---

## 5. Roadmap

| Phase | Description | Statut |
|-------|-------------|--------|
| 0 | Initialisation git + définition projet | ✅ En cours |
| 1 | Choix définitifs (stack, périmètre, données) | 🔲 À faire |
| 2 | Mise en place de l'environnement de dev | 🔲 À faire |
| 3 | Développement backend (API + IA) | 🔲 À faire |
| 4 | Développement frontend (interface) | 🔲 À faire |
| 5 | Tests avec données réelles | 🔲 À faire |
| 6 | Bilan : faisabilité, utilité, limites | 🔲 À faire |
| 7 | Préparation démo + diaporama | 🔲 À faire |

---

## 6. Bilan anticipé (à compléter)

### Gains attendus
- Réduction du temps de création de supports de formation
- Capitalisation automatique des connaissances internes
- Apprentissage actif et auto-évaluation des collaborateurs

### Limites anticipées
- Hallucinations du LLM → à mitiger avec RAG
- Qualité des quiz dépendante de la qualité du document source
- Coût API OpenAI (gérable avec un quota limité)
- Données sensibles / confidentielles de l'entreprise → anonymisation nécessaire

---

## 7. Questions ouvertes

- [ ] Quel est le contexte exact de l'alternance ? (secteur, taille équipe, type de docs)
- [ ] Utiliser OpenAI (payant) ou Ollama/Mistral (local, gratuit) ?
- [ ] Interface Streamlit (simple, rapide) ou Next.js (plus pro, plus long) ?
- [ ] Viser une démo en local ou déploiement cloud ?
