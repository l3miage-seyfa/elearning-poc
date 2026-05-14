# Architecture technique — SGC E-Learning IA

> Document de référence de la structure du code.  
> Mis à jour à chaque phase.

---

## Structure des dossiers

```
backend/
├── config/                  # Projet Django (settings, urls, wsgi)
│   ├── settings.py
│   ├── urls.py              # Routeur principal → 4 includes
│   └── wsgi.py
│
├── accounts/                # Utilisateurs / authentification
│   ├── models.py            # Person (OneToOne → User, is_admin)
│   ├── views.py             # login_view, logout_view, dashboard
│   ├── urls.py              # /accounts/
│   └── admin.py
│
├── groups/                  # Groupes et hiérarchie
│   ├── models.py            # Group, GroupMembership
│   ├── views.py             # my_groups, group_detail
│   ├── urls.py              # /groupes/
│   └── admin.py
│
├── courses/                 # Cours, slides, questions
│   ├── models.py            # Course, Slide, Question
│   ├── views.py             # admin_dashboard, member_courses, upload_pdf_view, course_detail
│   ├── urls.py              # /cours/
│   └── admin.py
│
├── participations/          # Historique et quiz
│   ├── models.py            # Participation
│   ├── views.py             # take_quiz, result
│   ├── urls.py              # /participations/
│   └── admin.py
│
├── services/                # Couche métier / IA (pas d'apps Django)
│   ├── __init__.py
│   ├── ai_service.py        # GPT-4o : extract_pdf_text, generate_slides, generate_questions
│   ├── storage_service.py   # Railway Bucket : upload_pdf, get_pdf_url
│   └── decorators.py        # @admin_required, @responsible_required, @login_and_person_required
│
└── templates/               # Templates HTML (Bootstrap 5 + Bootstrap Icons)
    ├── base.html             # Layout principal : navbar + sidebar dynamique
    ├── accounts/
    │   └── login.html        # Page de connexion (standalone, sans base.html)
    ├── courses/
    │   ├── admin_dashboard.html
    │   ├── member_courses.html
    │   ├── upload_pdf.html   # Drag & drop PDF + overlay progression IA
    │   ├── course_detail.html
    │   └── course_form.html  # Création manuelle (test)
    ├── groups/
    │   ├── my_groups.html
    │   └── group_detail.html
    └── participations/
        ├── quiz.html
        └── result.html
```

---

## URLs

| URL | Vue | Accès |
|-----|-----|-------|
| `/` | redirect → `accounts:dashboard` | Tous |
| `/accounts/login/` | `accounts:login_view` | Public |
| `/accounts/logout/` | `accounts:logout_view` | Connecté |
| `/accounts/dashboard/` | `accounts:dashboard` | Connecté |
| `/groupes/` | `groups:my_groups` | Membre |
| `/groupes/<pk>/` | `groups:group_detail` | Responsable / Admin |
| `/cours/admin/` | `courses:admin_dashboard` | Admin |
| `/cours/mes-cours/` | `courses:member_courses` | Membre |
| `/cours/upload-pdf/` | `courses:upload_pdf` | Admin |
| `/cours/upload-pdf/?course_id=X` | `courses:upload_pdf` (régénération) | Admin |
| `/cours/creer/` | `courses:course_create` | Admin |
| `/cours/<pk>/` | `courses:course_detail` | Membre |
| `/participations/quiz/<pk>/` | `participations:take_quiz` | Membre |
| `/participations/resultat/<pk>/` | `participations:result` | Membre |
| `/django-admin/` | Django Admin | Superuser |

---

## Modèles

### `accounts.Person`
```python
user        = OneToOneField(User)   # lié au User Django natif
is_admin    = BooleanField          # True uniquement pour admin@poc.com
```
> Accès via `request.user.person`

### `groups.Group`
```python
name        = CharField
description = TextField (optionnel)
type        = Enum [direction, equipe, projet]
parent      = FK(self, null=True)   # hiérarchie multi-niveaux
responsible = FK(Person)
members     = M2M(Person, via GroupMembership)
```
**Méthodes** :
- `save()` → ajoute automatiquement le responsable comme membre
- `get_ancestors()` → remonte la hiérarchie (pour héritage cours)

### `courses.Course`
```python
title        = CharField
group        = FK(Group)
created_by   = FK(Person)
pdf_file     = CharField            # clé S3 dans le bucket
nb_slides    = PositiveIntegerField
nb_questions = PositiveIntegerField
is_published = BooleanField         # False = invisible aux membres
created_at   = DateTimeField
```

### `courses.Slide`
```python
course  = FK(Course)
order   = PositiveIntegerField
content = TextField                 # texte markdown
```

### `courses.Question`
```python
course         = FK(Course)
order          = PositiveIntegerField
text           = TextField
choice_a/b/c/d = CharField
correct_answer = Enum [a, b, c, d]
explanation    = TextField
```

### `participations.Participation`
```python
person       = FK(Person)
course       = FK(Course)
score        = FloatField (null)    # null = quiz non encore soumis
completed_at = DateTimeField (null)
# unique_together: (person, course)
```

---

## Flux principal — Upload PDF → Cours publié

```
POST /cours/upload-pdf/
        │
        ▼
extract_pdf_text(pdf_bytes)          ← PyMuPDF
        │
        ▼
upload_pdf(pdf_bytes, filename)      ← Railway Bucket (S3) [optionnel en local]
        │
        ▼
generate_slides(pdf_text, nb)        ← GPT-4o → JSON [{order, content}, ...]
        │
        ▼
generate_questions(pdf_text, nb)     ← GPT-4o → JSON [{order, text, choice_*, correct_answer, explanation}, ...]
        │
        ▼
transaction.atomic():
  Course.objects.create(...)
  Slide.objects.bulk_create(...)
  Question.objects.bulk_create(...)
  course.is_published = True
        │
        ▼
redirect → /cours/<pk>/
```

---

## Logique d'accès aux cours (héritage hiérarchique)

Un membre a accès aux cours publiés de :
1. Ses groupes directs
2. Tous les groupes **ancêtres** (parents, grands-parents...)

```python
direct_groups = Group.objects.filter(members=person)
all_group_ids = set()
for group in direct_groups:
    all_group_ids.add(group.pk)
    for ancestor in group.get_ancestors():
        all_group_ids.add(ancestor.pk)

courses = Course.objects.filter(is_published=True, group_id__in=all_group_ids)
```

---

## Décorateurs d'accès (`services/decorators.py`)

| Décorateur | Condition |
|-----------|-----------|
| `@login_and_person_required` | Connecté + profil `Person` existant |
| `@admin_required` | `person.is_admin == True` |
| `@responsible_required` | Admin **ou** responsable d'au moins 1 groupe |

---

## Stack

| Composant | Technologie |
|-----------|-------------|
| Langage | Python 3.13.3 |
| Framework | Django 5.2 |
| Base locale | SQLite (dev) |
| Base prod | Railway PostgreSQL |
| PDF parsing | PyMuPDF (fitz) |
| LLM | OpenAI GPT-4o |
| Embeddings *(bonus)* | OpenAI text-embedding-3-small |
| Stockage fichiers | Railway Bucket (S3-compatible, boto3) |
| Frontend | Django Templates + Bootstrap 5.3 + Bootstrap Icons 1.11 |
| Déploiement | Railway (auto-deploy GitHub) |
| Variables d'env | python-decouple + fichier `.env` |
