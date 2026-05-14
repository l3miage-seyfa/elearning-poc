# Services — Documentation technique

> Couche `backend/services/` — fonctions métier appelables depuis n'importe quelle vue.  
> Ces modules ne sont **pas** des apps Django (pas de modèles, pas d'URLs).

---

## `ai_service.py` — Intelligence Artificielle

### `extract_pdf_text(pdf_bytes: bytes) → str`
Extrait le texte brut d'un fichier PDF en mémoire via **PyMuPDF**.

```python
from services.ai_service import extract_pdf_text
text = extract_pdf_text(open("doc.pdf", "rb").read())
```

- Concatène le texte de toutes les pages
- Retourne une chaîne vide si le PDF est scanné (pas de texte extractible)
- **Ne fait pas d'appel API**

---

### `generate_slides(pdf_text: str, nb_slides: int = 5) → list[dict]`
Génère des slides pédagogiques depuis le texte d'un PDF via **GPT-4o**.

**Retourne** :
```python
[
  {"order": 1, "content": "## Titre\n\n- **Point clé** : définition\n- Item 2"},
  {"order": 2, "content": "### Sous-section\n\n> Blockquote important"},
  ...
]
```

**Format Markdown imposé au prompt :**
- `##` titre principal, `###` sous-section
- `**gras**` pour les notions clés
- `- listes` à puces pour les points
- `*italique*` pour les nuances
- 5 à 10 lignes par slide, jamais de texte brut

**Paramètres** :
- `pdf_text` : texte brut du PDF (tronqué à 8 000 chars en interne)
- `nb_slides` : nombre de slides souhaité (1–20)

**Rendu côté frontend** : `marked.js` CDN via `json_script` + `JSON.parse()` (pas d'`escapejs`).  
**Format GPT-4o** : `response_format={"type": "json_object"}` — garantit un JSON valide.  
**Normalisation** : gère `{"slides": [...]}` ou `[...]` directement.

---

### `generate_questions(pdf_text: str, nb_questions: int = 5) → list[dict]`
Génère un QCM (4 choix, 1 bonne réponse) depuis le texte d'un PDF via **GPT-4o**.

**Retourne** :
```python
[
  {
    "order": 1,
    "text": "Quelle est la définition du RGPD ?",
    "choice_a": "...",
    "choice_b": "...",
    "choice_c": "...",
    "choice_d": "...",
    "correct_answer": "b",
    "explanation": "Le RGPD est..."
  },
  ...
]
```

**Paramètres** :
- `pdf_text` : texte brut du PDF (tronqué à 8 000 chars)
- `nb_questions` : nombre de questions souhaité (1–20)

---

### Variables d'environnement requises
```bash
OPENAI_API_KEY=sk-...
```
Si `OPENAI_API_KEY` est absent, le client OpenAI lève une `RuntimeError` à l'appel.

---

## `storage_service.py` — Stockage fichiers

Wrapper boto3 pour **Railway Storage Bucket** (S3-compatible).

### `upload_pdf(file_bytes: bytes, filename: str) → str`
Upload un fichier PDF dans le bucket et retourne la **clé S3** (chemin dans le bucket).

```python
from services.storage_service import upload_pdf
key = upload_pdf(open("doc.pdf", "rb").read(), "mon-doc.pdf")
# → "courses/pdfs/abc123_mon-doc.pdf"
```

La clé est stockée dans `Course.pdf_file`.

---

### `get_pdf_url(key: str, expires_in: int = 3600) → str`
Génère une **URL présignée** pour télécharger le PDF (expire après `expires_in` secondes).

```python
from services.storage_service import get_pdf_url
url = get_pdf_url("courses/pdfs/abc123_mon-doc.pdf")
# → "https://bucket.railway.app/courses/pdfs/abc123...?X-Amz-Signature=..."
```

### Variables d'environnement requises
```bash
AWS_S3_ENDPOINT_URL=https://...        # endpoint Railway Bucket
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=sgc-uploads
AWS_S3_REGION_NAME=auto
```

> En développement local, si ces variables sont absentes, `upload_pdf()` lève une exception silencieusement capturée dans `upload_pdf_view` — le cours est créé sans PDF stocké.

---

## `decorators.py` — Contrôle d'accès

### `@login_and_person_required`
Vérifie :
1. L'utilisateur est connecté (`request.user.is_authenticated`)
2. Il possède un profil `Person` (`request.user.person`)

Redirige vers `accounts:login` sinon.

---

### `@admin_required`
Vérifie en plus que `request.user.person.is_admin == True`.  
Redirige vers `accounts:dashboard` avec message d'erreur sinon.

---

### `@responsible_required`
Vérifie que la `Person` est admin **ou** responsable d'au moins un groupe.  
Usage : vues de gestion d'un groupe (voir les membres, etc.).

---

## Appel typique dans une vue

```python
from services.decorators import admin_required
from services.ai_service import extract_pdf_text, generate_slides, generate_questions
from services.storage_service import upload_pdf

@admin_required
def upload_pdf_view(request):
    pdf_bytes = request.FILES['pdf_file'].read()
    pdf_text  = extract_pdf_text(pdf_bytes)
    pdf_key   = upload_pdf(pdf_bytes, "cours.pdf")
    slides    = generate_slides(pdf_text, nb_slides=5)
    questions = generate_questions(pdf_text, nb_questions=5)
    # ... bulk_create + Course.save()
```
