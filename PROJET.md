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
**✅ OpenAI GPT-4o**
- API la plus capable et la mieux documentée
- Coût maîtrisé pour un POC (env. $5-15 selon usage)
- Librairie officielle `openai` en Python

### 3.2 Stack technique
**✅ CHOIX ACTÉ ET DÉFINITIF :**

```
LLM         : OpenAI GPT-4o (API)
Embeddings  : OpenAI text-embedding-3-small (pour RAG chatbot - phase bonus)
Backend     : Python 3.11 + Django (auth + ORM + admin intégrés)
Frontend    : Django Templates (HTML/Jinja2, sans CSS élaboré, tables simples)
BDD         : PostgreSQL sur AWS RDS (db.t3.micro - free tier)
              + extension pgvector (stockage vecteurs pour RAG - activée dès le début)
PDF parsing : PyMuPDF (fitz)
Fichiers    : AWS S3 (stockage persistant des PDFs uploadés)
Déploiement : AWS EC2 (t2.micro - free tier) + Gunicorn + Nginx
URL         : URL publique AWS (ex: http://ec2-xx-xx.compute.amazonaws.com)
```

> **Pourquoi pgvector et pas ChromaDB ?** pgvector est une **extension PostgreSQL** : pas de service supplémentaire à héberger. Les vecteurs sont stockés directement dans la base RDS existante. ChromaDB nécessiterait un serveur séparé sur EC2.

> **Pourquoi Django ?** Auth, panneau admin, ORM et gestion des sessions sont inclus nativement. Un seul projet à gérer.

> **Pourquoi RDS et pas SQLite ?** SQLite est un fichier stocké sur le disque de l'instance EC2. Si l'instance est arrêtée, recréée ou crashe → **toutes les données sont perdues**. RDS est un service de base de données indépendant de l'instance EC2 : les données survivent à tout redémarrage ou recréation du serveur.

> **Pourquoi S3 et pas fichiers locaux ?** Les fichiers stockés localement sur EC2 disparaissent avec l'instance. S3 est un stockage objet **permanent et indépendant** du serveur : les PDFs uploadés sont conservés même si l'instance EC2 est recréée.

### 3.3 Pattern IA utilisé
**✅ Deux patterns selon la fonctionnalité :**

**Phase principale — Prompt Engineering direct**
- Extraction du texte PDF via PyMuPDF
- Envoi du texte complet + prompt structuré à GPT-4o en un seul appel
- GPT-4o retourne un JSON avec slides + questions QCM + explications
- Limite : texte tronqué à ~50 000 tokens si PDF très long (largement suffisant)
- Pas de fine-tuning

**Phase bonus — RAG (Retrieval-Augmented Generation) pour chatbot**
- À la publication du cours, le texte du PDF est découpé en chunks
- Chaque chunk est transformé en vecteur via `OpenAI text-embedding-3-small`
- Les vecteurs sont stockés dans PostgreSQL via l'extension `pgvector`
- Quand un membre pose une question : sa question est vectorisée → recherche des chunks les plus proches → envoi à GPT-4o avec le contexte → réponse
- Implémenté via `django-pgvector` + `psycopg2`

---

## 4. Modèle de données ✅

### 4.1 Person (Utilisateur)
| Champ | Type | Contrainte |
|-------|------|-----------|
| `id` | Integer | PK, auto |
| `first_name` | String | requis |
| `last_name` | String | requis |
| `email` | String | unique, requis |
| `password` | String | hashé, saisi par l'admin à la création |
| `is_admin` | Boolean | `False` par défaut — seul `admin@poc.com` est `True` |

- Une personne peut être membre de plusieurs groupes
- Une personne peut être responsable de plusieurs groupes
- Une personne responsable d'un groupe en est **automatiquement membre**

---

### 4.2 Group (Groupe)
| Champ | Type | Contrainte |
|-------|------|-----------|
| `id` | Integer | PK, auto |
| `name` | String | requis |
| `description` | Text | optionnel |
| `type` | Enum | `direction` \| `equipe` \| `projet` |
| `parent` | FK → Group | nullable (groupe racine si null) |
| `responsible` | FK → Person | requis |
| `members` | M2M → Person | via table `GroupMembership` |

- Hiérarchie **multi-niveaux** (parent → enfant → petit-enfant...)
- Le responsable est automatiquement ajouté aux membres à la création/modification

---

### 4.3 Course (Cours)
| Champ | Type | Contrainte |
|-------|------|-----------|
| `id` | Integer | PK, auto |
| `title` | String | requis |
| `group` | FK → Group | requis (un cours appartient à un seul groupe) |
| `created_by` | FK → Person | responsable qui a créé le cours |
| `nb_slides` | Integer | configurable à la création |
| `nb_questions` | Integer | configurable à la création |
| `is_published` | Boolean | `False` jusqu'à validation par le responsable |
| `created_at` | DateTime | auto |

---

### 4.4 Slide (Page d'un cours)
| Champ | Type | Contrainte |
|-------|------|-----------|
| `id` | Integer | PK, auto |
| `course` | FK → Course | requis |
| `order` | Integer | numéro de la slide |
| `content` | Text | texte pur, éditable par le responsable |

---

### 4.5 Question (QCM d'un cours)
| Champ | Type | Contrainte |
|-------|------|-----------|
| `id` | Integer | PK, auto |
| `course` | FK → Course | requis |
| `order` | Integer | numéro de la question |
| `text` | Text | intitulé de la question |
| `choice_a` | String | requis |
| `choice_b` | String | requis |
| `choice_c` | String | requis |
| `choice_d` | String | requis |
| `correct_answer` | Enum | `a` \| `b` \| `c` \| `d` |
| `explanation` | Text | explication de la bonne réponse (générée par IA) |

- 4 choix par question, **1 seule bonne réponse**
- Éditable par le responsable avant publication

---

### 4.6 DocumentChunk (Phase bonus — RAG chatbot)
| Champ | Type | Contrainte |
|-------|------|-----------|
| `id` | Integer | PK, auto |
| `course` | FK → Course | requis |
| `chunk_index` | Integer | ordre du chunk dans le document |
| `content` | Text | texte brut du chunk |
| `embedding` | Vector(1536) | vecteur OpenAI (pgvector) |

- Généré automatiquement à la publication du cours
- Supprimé si le cours est supprimé (cascade)
- Utilisé uniquement par le chatbot

---

### 4.7 Participation (Historique d'un membre)
| Champ | Type | Contrainte |
|-------|------|-----------|
| `id` | Integer | PK, auto |
| `person` | FK → Person | requis |
| `course` | FK → Course | requis |
| `score` | Float | pourcentage (0.0 → 100.0) |
| `completed_at` | DateTime | auto |

- Contrainte unique : `(person, course)` → **une seule participation par personne par cours**
- Si le cours est modifié après participation, la note est **conservée telle quelle**

---

## 5. Rôles et droits ✅

### 5.1 Admin (`admin@poc.com`)
- Compte unique, créé au démarrage (`is_admin = True`)
- Accès au panneau d'administration Django (ou pages dédiées)
- Peut faire le **CRUD complet** sur : Personnes, Groupes

### 5.2 Responsable de groupe
- Est une `Person` ordinaire avec le rôle responsable sur un ou plusieurs groupes
- Dans l'interface **Mes groupes** : voit ses groupes + bouton "Créer un cours"
- Peut créer, modifier, supprimer les cours de **ses groupes uniquement**
- Voit la liste des membres de ses groupes et leurs participations

### 5.3 Membre ordinaire
- Dans **Mes cours** : voit tous les cours disponibles organisés par groupe (cours de ses groupes + cours des groupes parents, via héritage hiérarchique)
- Peut participer à un cours non encore complété
- Après participation, voit sa note en pourcentage
- **Ne peut pas refaire** un cours déjà complété

---

## 6. Logique d'accès aux cours (héritage hiérarchique) ✅

Un membre a accès aux cours de :
1. **Ses groupes directs** (groupes dont il est membre)
2. **Tous les groupes ancêtres** (parents, grands-parents...) de ses groupes directs

> Exemple : Marie est membre du groupe `Équipe Dev` (enfant de `Direction IT`, elle-même enfant de `Entreprise`). Marie voit les cours de `Équipe Dev` + `Direction IT` + `Entreprise`.

L'inverse **n'est pas vrai** : un membre d'un groupe parent ne voit **pas** les cours des groupes enfants.

---

## 7. Flow de création d'un cours ✅

```
1. Le responsable va sur la page de son groupe
2. Il clique "Créer un cours"
3. Il saisit : titre du cours, nombre de slides souhaité, nombre de questions souhaité
4. Il uploade un PDF
5. Le système extrait le texte du PDF (PyMuPDF)
6. Appel GPT-4o → génère N slides (texte pur)
7. Appel GPT-4o → génère M questions QCM avec explications
8. Le responsable visualise slide par slide → peut éditer le texte de chaque slide
9. Le responsable visualise chaque question → peut éditer l'intitulé, les choix, la bonne réponse
10. Il clique "Publier" → is_published = True → cours visible pour les membres
```

- Tant que `is_published = False`, le cours est **invisible pour les membres**
- Après publication, le responsable peut toujours **modifier ou supprimer** le cours
- Si le cours est modifié après des participations, les notes existantes sont **conservées**

---

## 8. Écrans de l'application ✅

### Interface Admin
| Écran | Description |
|-------|-------------|
| Login | Email + mot de passe |
| Dashboard admin | Vue d'ensemble : nb personnes, nb groupes, nb cours |
| Gestion personnes | Liste + Créer / Modifier / Supprimer une personne |
| Gestion groupes | Liste + Créer / Modifier / Supprimer un groupe (avec parent, responsable, membres) |

### Interface Membre / Responsable
| Écran | Description |
|-------|-------------|
| Login | Email + mot de passe |
| Mes cours | Tous les cours disponibles organisés par groupe, avec statut (non commencé / note %) |
| Mes groupes | Liste des groupes dont l'utilisateur est membre |
| Page groupe (responsable) | Liste des cours du groupe + bouton "Créer un cours" + liste membres |
| Créer un cours | Upload PDF + config nb slides/questions → génération IA → review/édition → publication |
| Passer un cours | Slides en lecture → quiz → résultats avec score % et explications |
| Chatbot cours *(bonus)* | Onglet sur la page cours : poser une question sur le contenu du PDF → réponse GPT-4o via RAG |

---

## 9. Roadmap détaillée avec estimations ✅

> **Légende temps** : estimation réaliste en heures de travail effectif (hors attentes/blocages)  
> **Total estimé** : ~33h phase principale + ~8h bonus + ~5h soutenance = **~46h**

---

### 🔧 PHASE 0 — Prérequis comptes & outils *(~2h)*
> **Avant de coder**, créer les comptes nécessaires

| Étape | Détail | Temps |
|-------|--------|-------|
| 0.1 | Créer compte **OpenAI** → générer une clé API (`sk-...`) → créditer $10 | 20 min |
| 0.2 | Créer compte **AWS** → activer free tier → créer un utilisateur IAM avec Access Key | 30 min |
| 0.3 | Installer **Python 3.11**, **pip**, **virtualenv** en local | 15 min |
| 0.4 | Installer **git**, configurer SSH key pour GitHub (ou GitLab) | 15 min |
| 0.5 | Tester la clé OpenAI avec un appel simple en Python | 20 min |

---

### 🏗️ PHASE 1 — Setup Django local *(~2h)*
> Projet Django fonctionnel en local avec tous les modèles créés

| Étape | Détail | Temps |
|-------|--------|-------|
| 1.1 | Créer le projet Django + app `core` + `requirements.txt` | 20 min |
| 1.2 | Configurer `settings.py` : base SQLite locale pour dev, variables d'env via `python-decouple` | 20 min |
| 1.3 | Écrire les **6 modèles** : `Person`, `Group`, `Course`, `Slide`, `Question`, `Participation` | 45 min |
| 1.4 | `makemigrations` + `migrate` + vérification admin Django | 15 min |
| 1.5 | Créer le superuser `admin@poc.com` via `createsuperuser` | 5 min |
| 1.6 | Enregistrer les modèles dans `admin.py` → vérifier le panneau admin | 15 min |

---

### 🔐 PHASE 2 — Authentification & routing *(~2h)*
> Login/logout fonctionnel, redirection selon le rôle

| Étape | Détail | Temps |
|-------|--------|-------|
| 2.1 | Configurer le système d'auth Django (LOGIN_URL, LOGIN_REDIRECT_URL) | 20 min |
| 2.2 | Page **login** (email + mot de passe) | 20 min |
| 2.3 | Middleware/décorateur : `@login_required` + `@admin_required` | 20 min |
| 2.4 | Redirection post-login : admin → dashboard admin, membre → Mes cours | 20 min |
| 2.5 | Page **logout** + navbar de base (Mes cours / Mes groupes / Déconnexion) | 20 min |

---

### 👤 PHASE 3 — Interface Admin : CRUD Personnes & Groupes *(~4h)*
> L'admin peut créer/modifier/supprimer personnes et groupes

| Étape | Détail | Temps |
|-------|--------|-------|
| 3.1 | Liste des personnes + formulaire **créer une personne** (nom, prénom, email, mdp) | 45 min |
| 3.2 | Modifier / Supprimer une personne | 30 min |
| 3.3 | Liste des groupes + formulaire **créer un groupe** (nom, description, type, parent, responsable, membres) | 60 min |
| 3.4 | Logique : ajout automatique du responsable comme membre | 20 min |
| 3.5 | Modifier / Supprimer un groupe | 30 min |
| 3.6 | Dashboard admin : compteurs (nb personnes, nb groupes, nb cours publiés) | 15 min |

---

### 📚 PHASE 4 — Interface Membre : Mes cours & Mes groupes *(~3h)*
> Un membre connecté voit ses cours disponibles et ses groupes

| Étape | Détail | Temps |
|-------|--------|-------|
| 4.1 | **Mes cours** : requête récursive pour remonter la hiérarchie des groupes ancêtres | 45 min |
| 4.2 | Affichage des cours par groupe, avec statut (non commencé / note %) | 30 min |
| 4.3 | **Mes groupes** : liste des groupes dont l'utilisateur est membre | 20 min |
| 4.4 | Si responsable d'un groupe : afficher liste des cours + bouton "Créer un cours" | 30 min |
| 4.5 | Page groupe responsable : liste des membres + leurs participations/notes | 30 min |

---

### 🤖 PHASE 5 — Génération IA : PDF → Slides + Quiz *(~4h)*
> Le cœur IA du projet : un PDF devient un cours complet

| Étape | Détail | Temps |
|-------|--------|-------|
| 5.1 | Extraction du texte PDF avec **PyMuPDF** + nettoyage | 30 min |
| 5.2 | Écrire le **prompt slides** : instructions GPT-4o pour générer N slides en JSON | 45 min |
| 5.3 | Écrire le **prompt questions** : instructions GPT-4o pour générer M QCM en JSON | 45 min |
| 5.4 | Appels API OpenAI + parsing JSON + gestion erreurs | 30 min |
| 5.5 | Sauvegarder slides et questions en base | 20 min |
| 5.6 | Tests avec 2-3 PDFs différents, ajustement des prompts | 30 min |

---

### 📝 PHASE 6 — Flow création de cours *(~4h)*
> Le responsable crée, revoit, corrige et publie un cours

| Étape | Détail | Temps |
|-------|--------|-------|
| 6.1 | Formulaire **créer un cours** : titre + nb slides + nb questions + upload PDF | 30 min |
| 6.2 | Upload du PDF vers **AWS S3** via `boto3` | 30 min |
| 6.3 | Lancement de la génération IA (appel phases 5.1→5.5) | 20 min |
| 6.4 | Page **review slides** : affichage slide par slide avec formulaire d'édition du texte | 45 min |
| 6.5 | Page **review questions** : affichage question par question avec édition | 45 min |
| 6.6 | Bouton **Publier** → `is_published = True` → cours visible | 15 min |
| 6.7 | Modifier / Supprimer un cours publié | 20 min |

---

### 🎯 PHASE 7 — Flow participation : passer un cours *(~3h)*
> Un membre passe un cours, voit ses slides, répond au quiz, obtient sa note

| Étape | Détail | Temps |
|-------|--------|-------|
| 7.1 | Page **lecture slides** : navigation slide par slide (précédent / suivant) | 30 min |
| 7.2 | Page **quiz** : affichage des questions QCM avec boutons radio | 45 min |
| 7.3 | Soumission quiz : calcul du score en % + création de la `Participation` | 30 min |
| 7.4 | Page **résultats** : score % + pour chaque question bonne/mauvaise réponse + explication | 30 min |
| 7.5 | Bloquer la re-participation si déjà une note | 15 min |

---

### ☁️ PHASE 8 — Déploiement AWS *(~6h)*
> L'application tourne en ligne avec une URL publique

| Étape | Détail | Temps |
|-------|--------|-------|
| 8.1 | Créer instance **EC2 t2.micro** Ubuntu + configurer Security Group (ports 22, 80) | 30 min |
| 8.2 | Créer base **RDS PostgreSQL** + activer extension `pgvector` | 30 min |
| 8.3 | Créer **bucket S3** + configurer les permissions IAM | 20 min |
| 8.4 | SSH sur EC2 : installer Python, pip, virtualenv, Nginx, Gunicorn | 30 min |
| 8.5 | Cloner le repo + configurer `.env` (clés OpenAI, AWS, DB) | 20 min |
| 8.6 | Adapter `settings.py` pour PostgreSQL + S3 en production | 30 min |
| 8.7 | `migrate` + `collectstatic` + créer superuser en prod | 15 min |
| 8.8 | Configurer **Gunicorn** comme service systemd | 30 min |
| 8.9 | Configurer **Nginx** comme reverse proxy | 30 min |
| 8.10 | Tests complets sur l'URL publique + debug | 45 min |

---

### 🤖 PHASE 9 — [BONUS] Chatbot RAG *(~8h)*
> Ajouté seulement si les phases 1-8 sont terminées

| Étape | Détail | Temps |
|-------|--------|-------|
| 9.1 | Activer `pgvector` dans PostgreSQL + modèle `DocumentChunk` | 30 min |
| 9.2 | À la publication : découper le texte PDF en chunks de ~500 tokens | 30 min |
| 9.3 | Appel `text-embedding-3-small` pour chaque chunk + stockage pgvector | 45 min |
| 9.4 | Fonction de recherche sémantique : vectoriser la question → top-K chunks | 45 min |
| 9.5 | Appel GPT-4o avec contexte + question → réponse | 30 min |
| 9.6 | Interface chatbot sur la page cours (zone de saisie + historique) | 90 min |
| 9.7 | Tests + ajustements | 60 min |

---

### 🎓 PHASE 10 — Bilan & Soutenance *(~5h)*

| Étape | Détail | Temps |
|-------|--------|-------|
| 10.1 | Rédiger le bilan : faisabilité, utilité, limites, recommandations | 90 min |
| 10.2 | Préparer le **diaporama** (slides de présentation) | 90 min |
| 10.3 | Préparer le **scénario de démo** (données réalistes) | 60 min |
| 10.4 | Répétition de la présentation (15 min exposé + 5 min questions) | 60 min |

---

### 📊 Récapitulatif des temps

| Phase | Description | Temps estimé |
|-------|-------------|-------------|
| 0 | Prérequis comptes & outils | ~2h |
| 1 | Setup Django local | ~2h |
| 2 | Auth & routing | ~2h |
| 3 | Admin CRUD | ~4h |
| 4 | Interface membre | ~3h |
| 5 | Génération IA (PDF → cours) | ~4h |
| 6 | Flow création cours | ~4h |
| 7 | Flow participation | ~3h |
| 8 | Déploiement AWS | ~6h |
| 9 | **[BONUS]** Chatbot RAG | ~8h |
| 10 | Bilan & soutenance | ~5h |
| **TOTAL sans bonus** | | **~35h** |
| **TOTAL avec bonus** | | **~43h** |

---

---

## 10. Architecture de déploiement AWS ✅

### Infrastructure cible

```
┌─────────────────────────────────────────────────────┐
│                      AWS Cloud                       │
│                                                     │
│   ┌──────────────┐        ┌───────────────────┐    │
│   │  EC2 t2.micro │        │   RDS PostgreSQL   │    │
│   │  (free tier)  │◄──────►│   (free tier)     │    │
│   │               │        └───────────────────┘    │
│   │  Nginx        │                                  │
│   │  Gunicorn     │        ┌───────────────────┐    │
│   │  Django app   │◄──────►│   S3 Bucket       │    │
│   └──────────────┘        │  (PDFs uploadés)  │    │
│          │                 └───────────────────┘    │
│          │ URL publique                              │
└──────────┼──────────────────────────────────────────┘
           │
     http://ec2-xx-xx-xx-xx.compute.amazonaws.com
```

### Services AWS utilisés

| Service | Usage | Coût estimé |
|---------|-------|-------------|
| **EC2 t2.micro** | Serveur applicatif Django + Gunicorn + Nginx | Gratuit (free tier 12 mois) |
| **RDS PostgreSQL** (db.t3.micro) | Base de données | Gratuit (free tier 12 mois) |
| **S3** | Stockage des PDFs uploadés + fichiers statiques | ~$0 pour un POC |
| **Security Groups** | Firewall : ports 80 (HTTP) et 22 (SSH) ouverts | Gratuit |

### Stack serveur sur EC2
```
OS          : Ubuntu 22.04 LTS
Serveur web : Nginx (reverse proxy)
WSGI        : Gunicorn
App         : Django
Process mgr : systemd (ou supervisor)
Env vars    : fichier .env sur le serveur (clé OpenAI, DB password...)
```

### Variables d'environnement à configurer
```bash
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=ec2-xx-xx-xx-xx.compute.amazonaws.com
DATABASE_URL=postgres://user:password@rds-endpoint:5432/doculearn
OPENAI_API_KEY=sk-...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET_NAME=doculearn-uploads
```

### Étapes de déploiement (résumé)
1. Créer une instance EC2 t2.micro (Ubuntu)
2. Créer une base RDS PostgreSQL (free tier)
3. Créer un bucket S3 pour les uploads
4. Installer Python, Nginx, Gunicorn sur EC2
5. Cloner le repo git sur EC2
6. Configurer le `.env` avec les variables
7. `python manage.py migrate` + `collectstatic`
8. Configurer Gunicorn comme service systemd
9. Configurer Nginx comme reverse proxy
10. Ouvrir le port 80 dans le Security Group

---

## 11. Bilan anticipé

### Gains attendus
- Création de modules de formation depuis un PDF en quelques minutes
- Capitalisation automatique des connaissances documentaires internes
- Apprentissage actif et auto-évaluation structurée par groupe/équipe
- Suivi simple de la progression des membres par les responsables

### Limites anticipées
- Qualité des slides/quiz dépendante de la clarté du document source
- Hallucinations GPT-4o → le responsable doit relire avant publication
- Coût API OpenAI → gérable avec un quota (token limit par requête)
- Confidentialité → ne pas uploader de documents sensibles sans accord
- Pas de système de rappel mémoriel (hors périmètre POC)
- Interface minimaliste (pas de CSS élaboré, volontaire pour POC)
