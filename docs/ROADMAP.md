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

## Phase 3 — CRUD Admin : Personnes & Groupes 🔲

> L'admin peut créer / modifier / supprimer des personnes et des groupes depuis l'interface web (pas uniquement via Django admin).

- [ ] Vue + formulaire **créer une personne** (nom, prénom, email, mot de passe)
- [ ] Vue **modifier / supprimer** une personne
- [ ] Vue + formulaire **créer un groupe** (nom, description, type, parent, responsable, membres)
- [ ] Logique : ajout automatique du responsable comme membre (déjà dans `Group.save()`)
- [ ] Vue **modifier / supprimer** un groupe
- [ ] Dashboard admin : compteurs (nb personnes, nb groupes, nb cours publiés)

---

## Phase 4 — Interface Responsable de groupe 🔲

> Un responsable voit les membres de son groupe, leurs participations, et peut gérer les cours.

- [ ] Page groupe responsable : liste des membres + leurs participations + scores
- [ ] Bouton "Créer un cours" depuis la page groupe (lien vers `upload_pdf`)
- [ ] Restreindre l'édition/suppression des cours aux seuls responsables du groupe concerné

---

## Phase 5 — Review & édition des slides/questions 🔲

> Avant publication, le responsable peut corriger chaque slide et chaque question.

- [ ] Page **review slides** : affichage slide par slide, formulaire d'édition inline
- [ ] Page **review questions** : affichage question par question, édition intitulé + choix + bonne réponse
- [ ] Bouton **Publier** sur la page de review (plutôt que publication automatique)
- [ ] Modifier `upload_pdf_view` : ne plus publier automatiquement, rediriger vers la review

---

## Phase 6 — Flow participation amélioré 🔲

> Navigation slide par slide, résultats détaillés par question.

- [ ] Page **lecture slides** : navigation précédent / suivant (actuellement accordion statique)
- [ ] Page **résultats détaillés** : pour chaque question, afficher bonne/mauvaise réponse + explication
- [ ] Historique des participations dans "Mes cours"

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

**→ Phase 3** : CRUD web pour Personnes et Groupes + dashboard admin avec compteurs.
