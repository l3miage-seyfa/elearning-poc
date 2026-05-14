# 📋 PROJET.md — Définition du POC E-Learning IA

## 1. Contexte & Problématique

### Contexte
Dans le cadre du cours **Systèmes de Gestion des Connaissances** (M2 MIAGE), nous devons réaliser un POC basé sur la technologie de **e-learning utilisant une IA générative**.

### Problématique générale
> Comment une équipe ou un service peut-il capitaliser et transmettre ses connaissances internes de façon efficace, personnalisée et automatisée grâce à un LMS augmenté par l'IA ?

---

## 2. Analyse des outils existants (recherche 14/05/2026)

> Voir [Technologie.md](Technologie.md) pour l'analyse complète de Docebo, CoorpAcademy et Domoscio.

### Synthèse des fonctionnalités clés du marché

| Fonctionnalité | Qui le fait | Pertinence POC |
|----------------|-------------|---------------|
| Génération de cours depuis un PDF/doc | Docebo Creator | ⭐⭐⭐ Très forte |
| Quiz automatiques depuis un contenu | Docebo, CoorpAcademy, Domoscio | ⭐⭐⭐ Très forte |
| Chatbot pédagogique (Q&A sur contenu) | Docebo Harmony Tutor | ⭐⭐⭐ Très forte |
| Résumé de document | Docebo Harmony | ⭐⭐⭐ Très forte |
| Parcours adaptatif (niveau détecté) | Domoscio Hub | ⭐⭐ Forte, complexe |
| Ancrage mémoriel / rappels espacés | Domoscio Lock | ⭐⭐ Forte, complexe |
| Gamification / Battle | CoorpAcademy | ⭐ Secondaire |

---

## 3. Choix techniques actés ✅

> Ces choix sont **définitifs** et doivent être respectés dans tout le développement.

### 3.1 LLM / Moteur IA
**✅ CHOIX ACTÉ : OpenAI GPT-4o**
- API la plus capable et la mieux documentée
- Support natif du traitement de documents (texte extrait)
- Coût maîtrisé pour un POC (env. $5-15 selon usage)
- Librairie officielle `openai` en Python

### 3.2 Fonctionnalités du POC
**✅ CHOIX ACTÉ : Combinaison inspirée de Docebo Creator + Harmony Tutor**

L'application permettra à un utilisateur de :
1. **Uploader un document interne** (PDF ou texte) → extraction du contenu
2. **Générer un résumé structuré** du document via GPT-4o
3. **Générer un quiz QCM** (5 à 10 questions) basé sur le contenu du document
4. **Passer le quiz interactif** et voir son score avec les corrections expliquées par l'IA
5. **(Bonus)** Poser des questions au document via un chatbot (RAG)

> Ces fonctionnalités correspondent exactement à ce que fait **Docebo Creator + Harmony Tutor** mais dans une version POC autonome.

### 3.3 Stack technique
**✅ CHOIX ACTÉ :**

```
LLM         : OpenAI GPT-4o (API)
Backend     : Python 3.11 + FastAPI
Frontend    : Streamlit (rapidité de développement pour POC)
RAG/Vecteurs: LangChain + ChromaDB (si chatbot activé)
BDD         : SQLite (léger, suffisant pour POC)
PDF parsing : PyMuPDF (fitz) ou pdfplumber
Déploiement : Local (démo en live)
```

### 3.4 Pattern IA utilisé
**✅ CHOIX ACTÉ : Prompt Engineering + RAG (optionnel)**
- Génération de quiz et résumés : **Prompt Engineering** structuré (rapide, efficace)
- Chatbot Q&A : **RAG avec ChromaDB** (le document est indexé, l'IA répond en s'y référant)
- Pas de fine-tuning (trop lourd pour un POC)

---

## 4. Périmètre du POC — Application "DocuLearn"

> **Nom provisoire** : DocuLearn  
> *Un outil qui transforme n'importe quel document interne en module de formation interactif*

### Scénario utilisateur (User Story principale)
> En tant que **collaborateur**, je veux **uploader un document interne** (procédure, guide, note) pour **obtenir un résumé + un quiz auto-généré** et **tester ma compréhension**, afin de **monter en compétences rapidement** sur ce sujet.

### Écrans de l'application
1. **Page d'accueil** : Upload de document (PDF ou texte)
2. **Page résumé** : Affichage du résumé structuré généré par l'IA
3. **Page quiz** : QCM interactif (5-10 questions) avec bouton "Valider"
4. **Page résultats** : Score + corrections détaillées expliquées par l'IA
5. **(Bonus) Chat** : Interface de questions/réponses sur le document

### Ce que ça démontre pour la gestion des connaissances
- ✅ **Capitalisation** : Les documents internes deviennent des ressources pédagogiques
- ✅ **Transfert de connaissances** : Les collaborateurs apprennent activement via quiz
- ✅ **Gain de temps** : Plus besoin de créer manuellement des supports de formation
- ✅ **Scalabilité** : Fonctionne sur n'importe quel document

---

## 5. Questions encore ouvertes

- [ ] **Contexte alternance** : Quel secteur ? Quel type de documents disponibles ? (procédures internes, wikis, fiches techniques ?)
- [ ] **Données de démo** : Quels documents utiliser pour la démo ? (anonymisés si besoin)
- [ ] **Déploiement** : Local suffit pour la soutenance ? Ou hébergement cloud souhaité ?

---

## 6. Roadmap

| Phase | Description | Statut |
|-------|-------------|--------|
| 0 | Initialisation git + structure projet | ✅ Fait |
| 1 | Recherche outils existants + choix définitifs | ✅ Fait (14/05/2026) |
| 2 | Setup environnement Python + clé OpenAI | 🔲 À faire |
| 3 | Backend : extraction PDF + appels GPT-4o (résumé + quiz) | 🔲 À faire |
| 4 | Frontend Streamlit : upload + affichage résumé + quiz | 🔲 À faire |
| 5 | Intégration complète + tests avec docs réels | 🔲 À faire |
| 6 | (Bonus) Chatbot RAG avec ChromaDB | 🔲 À faire |
| 7 | Bilan : faisabilité, utilité, limites | 🔲 À faire |
| 8 | Préparation démo + diaporama soutenance | 🔲 À faire |

---

## 7. Bilan anticipé

### Gains attendus
- Réduction drastique du temps de création de supports de formation
- Capitalisation automatique des connaissances documentaires internes
- Apprentissage actif et auto-évaluation pour les collaborateurs
- Accessible sans compétences techniques (simple upload de document)

### Limites anticipées
- Hallucinations du LLM → à mitiger avec des prompts stricts et le RAG
- Qualité des quiz dépendante de la qualité et clarté du document source
- Coût API OpenAI → gérable avec un quota (token limit par requête)
- Confidentialité des documents → ne pas envoyer de données sensibles sans accord
- Pas de suivi de progression long terme (hors périmètre POC)
