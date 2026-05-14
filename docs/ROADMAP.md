# Roadmap — POC SGC E-Learning IA

> Suivi de l'avancement des phases de développement.  
> Légende : ✅ Terminé · 🔄 En cours · 🔲 Non démarré

---

## Phase 0 — Prérequis comptes & outils ✅

- [x] Compte OpenAI créé, clé API `sk-...` générée
- [x] Compte Railway créé, repo GitHub connecté
- [x] Python 3.13.3 installé, `venv` configuré
- [x] Clé OpenAI testée (appel GPT-4o fonctionnel)

---

## Phase 1 — Setup Django & modèles ✅

- [x] Projet Django 5.2 créé dans `backend/`
- [x] Architecture modulaire : 4 apps (`accounts`, `groups`, `courses`, `participations`)
- [x] `services/` : `ai_service.py`, `storage_service.py`, `decorators.py`
- [x] Tous les modèles écrits et migrés
- [x] Admin Django enrichi (inlines, actions, filtres)
- [x] Superuser `admin@poc.com` / `admin1234` créé
- [x] Templates Bootstrap 5 + Bootstrap Icons (sans emojis)
- [x] `config/urls.py` : 4 includes + redirect racine
- [x] **Commit** : `ce54c6b` — refactor architecture modulaire

**Modèles créés :**
| App | Modèles |
|-----|---------|
| `accounts` | `Person` |
| `groups` | `Group`, `GroupMembership` |
| `courses` | `Course`, `Slide`, `Question` |
| `participations` | `Participation` |

---

## Phase 2 — Upload PDF + Génération IA ✅

- [x] `services/ai_service.py` : `extract_pdf_text()`, `generate_slides()`, `generate_questions()`
- [x] `services/storage_service.py` : `upload_pdf()`, `get_pdf_url()`
- [x] Vue `courses/upload_pdf_view` — flux complet PDF → slides + quiz
- [x] Mode **nouveau cours** (titre + groupe saisis)
- [x] Mode **régénération** d'un cours existant (`?course_id=X`)
- [x] Template `upload_pdf.html` : drag & drop, overlay de progression
- [x] Transaction atomique : `bulk_create` slides + questions + `is_published = True`
- [x] Bouton "Upload PDF + IA" dans sidebar et dashboard admin
- [x] PyMuPDF + boto3 installés dans le venv
- [x] **Commit** : `57f617f` — feat Phase 2

---

## Phase 3 — CRUD Admin : Personnes & Groupes ✅

- [x] Vue + formulaire **créer une personne** (nom, prénom, email, mot de passe)
- [x] Vue **modifier / supprimer** une personne
- [x] Vue + formulaire **créer un groupe** (nom, description, type, parent, responsable, membres)
- [x] Logique : ajout automatique du responsable comme membre (`Group.save()`)
- [x] Vue **modifier / supprimer** un groupe
- [x] Dashboard admin : compteurs (nb personnes, nb groupes, nb cours publiés)
- [x] **Commit** : `70c36bc`

---

## Phase 4 — Interface Responsable de groupe ✅

- [x] Page groupe responsable : liste membres + participations + scores
- [x] Ajout/retrait de membres via email avec autocomplete live
- [x] Bouton "Gérer" dans "Mes groupes" → page responsable
- [x] Boutons Publier/Dépublier/Supprimer cours inline
- [x] **Commit** : `a764fa6`, `5e25ba2`

---

## Phase 5 — Review & édition des slides/questions ✅

- [x] Page **review slides** : édition textarea par slide
- [x] Page **review questions** : édition énoncé + choix + bonne réponse + explication
- [x] Bouton **Publier / Dépublier** (toggle) sur la page de review et la page détail
- [x] `upload_pdf_view` ne publie plus automatiquement → redirige vers review
- [x] **Commit** : `a764fa6`, `c96173e`

---

## Phase 6 — Flow participation amélioré ✅

- [x] Page **lecture slides** : navigation Précédent/Suivant avec barre de progression et dots
- [x] Page **résultats détaillés** : pour chaque question, bonne/mauvaise réponse surlignée + explication
- [x] Champ `answers` (JSON) ajouté sur `Participation` — migration `0002`
- [x] **Historique** des participations : `/participations/historique/` avec lien vers chaque résultat détaillé
- [x] Bouton "Mon historique" dans sidebar + dans "Mes cours"
- [x] "Mes cours" : bouton **Lire** (slides) + bouton **Résultats** (si déjà passé)
- [x] **Commit** : `HEAD`

---

## Phase 7 — Déploiement Railway 🔲

- [ ] Variables d'env configurées sur Railway
- [ ] `settings.py` : `DATABASE_URL`, `STORAGES` Railway Bucket, `ALLOWED_HOSTS`, `STATIC_ROOT`
- [ ] `python manage.py collectstatic` intégré au build
- [ ] `git push` → déploiement automatique vérifié
- [ ] Migrations jouées sur la base PostgreSQL Railway
- [ ] Superuser recréé en production
- [ ] Tests complets sur URL publique `https://xxx.railway.app`

---

## Phase 8 — [BONUS] Chatbot RAG 🔲

> Posez une question sur le contenu d'un cours → réponse GPT-4o contextuelle.

- [ ] Extension `pgvector` activée sur Railway PostgreSQL
- [ ] Modèle `DocumentChunk` (`course FK`, `chunk_index`, `content`, `embedding Vector(1536)`)
- [ ] Découpage du texte PDF en chunks à la publication
- [ ] Vectorisation des chunks via `text-embedding-3-small`
- [ ] Recherche sémantique : question → top-K chunks → GPT-4o
- [ ] Interface chatbot sur la page cours

---

## Phase 9 — Bilan & Soutenance 🔲

- [ ] Rédiger le bilan (`docs/BILAN.md`) : faisabilité, utilité, limites, recommandations
- [ ] Diaporama de présentation (15 min)
- [ ] Scénario de démo avec données réalistes
- [ ] Répétition

---

## Prochaine action immédiate

**→ Phase 7** : Déploiement Railway (variables d'env, PostgreSQL, collectstatic, tests prod).
