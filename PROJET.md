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
**✅ CHOIX ACTÉ :**

```
LLM         : OpenAI GPT-4o (API)
Backend     : Python 3.11 + Django (auth + ORM + admin intégrés)
Frontend    : Django Templates (HTML/Jinja2, sans CSS élaboré, tables simples)
BDD         : SQLite (léger, suffisant pour POC)
PDF parsing : PyMuPDF (fitz)
Déploiement : Local (démo en live)
```

> **Pourquoi Django ?** Auth, panneau admin, ORM et gestion des sessions sont inclus nativement. Pas de deux serveurs à gérer. Idéal pour un POC avec plusieurs rôles et entités.

### 3.3 Pattern IA utilisé
**✅ Prompt Engineering structuré**
- Génération des slides : envoi du texte extrait du PDF + instructions précises à GPT-4o
- Génération des questions QCM : prompt séparé, nombre configurable
- Pas de RAG, pas de fine-tuning (hors périmètre POC)

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

### 4.6 Participation (Historique d'un membre)
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

---

## 9. Roadmap ✅

| Phase | Description | Statut |
|-------|-------------|--------|
| 0 | Initialisation git + structure projet | ✅ Fait |
| 1 | Recherche outils existants + choix définitifs | ✅ Fait (14/05/2026) |
| 2 | Spécification complète (ce document) | ✅ Fait (14/05/2026) |
| 3 | Setup Django + modèles + migrations + admin | 🔲 À faire |
| 4 | Auth (login/logout, redirect selon rôle) | 🔲 À faire |
| 5 | Interface Admin : CRUD Personnes & Groupes | 🔲 À faire |
| 6 | Interface Membre : Mes cours + Mes groupes | 🔲 À faire |
| 7 | Génération IA : extraction PDF + appels GPT-4o | 🔲 À faire |
| 8 | Flow création cours : upload → génération → édition → publication | 🔲 À faire |
| 9 | Flow participation : slides → quiz → résultats | 🔲 À faire |
| 10 | Tests avec données réelles | 🔲 À faire |
| 11 | Bilan : faisabilité, utilité, limites | 🔲 À faire |
| 12 | Préparation démo + diaporama soutenance | 🔲 À faire |

---

## 10. Bilan anticipé

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
