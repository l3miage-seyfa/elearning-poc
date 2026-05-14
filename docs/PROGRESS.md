# Journal de développement

> Décisions techniques, problèmes rencontrés, solutions retenues.  
> Ordre chronologique — le plus récent en bas.

---

## 10/05/2026 — Initialisation du projet

**Décisions prises :**
- Stack choisie : Django 5.2 + Railway + OpenAI GPT-4o (voir [PROJET.md](../PROJET.md) §3)
- Abandon AWS EC2 → Railway : déploiement automatique depuis GitHub, pgvector inclus
- Abandon AWS S3 → Railway Bucket : même API boto3, zéro compte AWS

**Résultat :** Structure de dossiers créée, dépôt GitHub initialisé.

---

## 14/05/2026 — Phase 1 : Django monolithique

**Commit :** `0fc3f87`  
**Ce qui a été fait :**
- Projet Django dans `backend/`, app `core/` avec 6 modèles
- Migrations, superuser `admin@poc.com`, admin Django enregistré
- Templates basiques

**Problème :** App `core/` trop grosse — models.py, views.py, urls.py devenaient difficiles à maintenir.

**Décision :** Refactoring immédiat vers architecture modulaire (4 apps séparées).

---

## 14/05/2026 — Refactoring : architecture modulaire

**Commit :** `ce54c6b`  
**Ce qui a été fait :**
- 4 apps Django créées : `accounts`, `groups`, `courses`, `participations`
- Dossier `services/` : couche métier sans modèles ni URLs
- Templates réorganisés par app dans `backend/templates/`
- `config/urls.py` : 4 includes + redirect racine
- `core/` supprimé du dépôt
- Migrations régénérées proprement (db.sqlite3 recréée)
- Superuser recréé avec profil `Person.is_admin=True`
- Bootstrap Icons remplace tous les emojis dans les templates

**Décision : publication automatique à l'upload**  
Pour simplifier le POC, `is_published = True` est mis automatiquement après génération IA.  
La phase 5 (review avant publication) ajoutera un bouton "Publier" manuel.

---

## 14/05/2026 — Phase 2 : Upload PDF + Génération IA

**Commit :** `57f617f`  
**Ce qui a été fait :**
- `services/ai_service.py` : `extract_pdf_text` (PyMuPDF), `generate_slides`, `generate_questions` (GPT-4o)
- `services/storage_service.py` : `upload_pdf`, `get_pdf_url` (boto3 S3-compatible)
- Vue `courses/upload_pdf_view` : flux complet en mode nouveau cours **et** régénération
- Template `upload_pdf.html` : drag & drop, overlay animé pendant la génération IA
- `bulk_create` pour slides et questions (transaction atomique)
- boto3 + PyMuPDF installés dans le venv

**Choix de prompts :**
- `response_format={"type": "json_object"}` → JSON garanti valide côté OpenAI
- Texte tronqué à 8 000 chars (largement suffisant pour des PDFs de cours)
- `temperature=0.7` pour les slides (créativité), `0.5` pour les questions (précision)

**Comportement storage en local :**  
Si les variables `AWS_*` ne sont pas dans `.env`, `upload_pdf()` lève une exception  
capturée silencieusement — le cours est créé sans PDF stocké. Normal en dev.

---

## Prochaines décisions à prendre

### Phase 3 — CRUD Personnes & Groupes
**Question :** Utiliser Django Admin existant ou créer des vues custom ?  
**Recommandation :** Vues custom pour une expérience utilisateur cohérente avec le reste de l'app (même layout `base.html`). L'admin Django reste disponible en fallback.

### Phase 5 — Review avant publication
**Question :** Inline dans une seule page ou page par slide ?  
**Réponse retenue :** Page unique avec formulaire multi-champs.

### Phase 7 — Déploiement Railway
**À faire avant le déploiement :**
1. `python manage.py collectstatic` → dossier `staticfiles/`
2. Ajouter `STATIC_ROOT` dans `settings.py`
3. Vérifier `ALLOWED_HOSTS` = `['*.railway.app']`
4. Activer l'extension pgvector sur Railway avant les migrations

---

## 14/05/2026 — Phases 3–6 + améliorations UX

**Commits :** `70c36bc` → `165fe01`  
**Ce qui a été fait :**
- CRUD Personnes & Groupes avec vues Bootstrap
- Interface responsable de groupe : membres, fichiers, participations, cours
- Ajout/retrait membres via autocomplete email
- Wizard création cours (PDF → IA → slides + questions)
- Review slides/questions avant publication
- Lecture slides avec navigation + barre de progression
- **Rendu Markdown** des slides via `marked.js` (CDN) — h1–h4, listes, bold, code, blockquote, tableaux
- **Mode aperçu responsable** : même vue `slide_reader` avec 3 contextes (`back=slides/group/admin`)
- **Multi-tentatives** : suppression `unique_together` sur `Participation` + migration `0003`
- Historique participations avec numéro de tentative + bouton Repasser
- Description groupe éditable depuis la page responsable
- Messages flash dédupliqués (un seul bloc dans `base.html`)
- **56 tests structurés** dans `app/__tests__/` — 56/56 ✅
- Nettoyage : templates/vues/routes morts supprimés
- Prompt IA enrichi : Markdown structuré imposé (`##`, `###`, `**`, `- listes`)

**Problèmes rencontrés :**
- `escapejs` dans `data-raw` double-échappait les caractères (`\r\n` → `\u000D\u000A`) → fix : `json_script` + `JSON.parse()`
- `slide_reader` faisait `get_object_or_404(is_published=True)` avant de lire `?preview=1` → fix : vérifier `preview` en premier
- Messages affichés deux fois : bloc `messages` dans templates enfants + `base.html` → supprimé des enfants
