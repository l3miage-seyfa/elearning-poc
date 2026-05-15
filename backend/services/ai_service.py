"""
AI Service — wrappers OpenAI GPT-4o pour génération de contenu pédagogique.
Toutes les fonctions retournent des structures Python prêtes à sauvegarder en BDD.
"""
import json
from django.conf import settings

try:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
except Exception:
    client = None


# Limite de texte extrait par source (chars) et total pour ne pas dépasser le contexte GPT-4o
_CHARS_PER_SOURCE = 5000
_CHARS_TOTAL_MAX  = 14000


def extract_pdf_text(pdf_source) -> str:
    """
    Extrait le texte d'un ou plusieurs PDFs.
    - Si `pdf_source` est un bytes  → un seul PDF
    - Si `pdf_source` est une list[bytes] → plusieurs PDFs, textes séparés par ---SOURCE N---
    """
    import fitz  # PyMuPDF

    sources = pdf_source if isinstance(pdf_source, list) else [pdf_source]
    parts: list[str] = []

    for i, raw in enumerate(sources, start=1):
        doc  = fitz.open(stream=raw, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc).strip()
        text = text[:_CHARS_PER_SOURCE]          # limite par source
        if len(sources) > 1:
            parts.append(f"=== SOURCE {i} ===\n{text}")
        else:
            parts.append(text)

    combined = "\n\n".join(parts)
    return combined[:_CHARS_TOTAL_MAX]           # limite totale


def _source_note(pdf_source) -> str:
    """Phrase contextuelle à injecter dans les prompts quand plusieurs sources."""
    n = len(pdf_source) if isinstance(pdf_source, list) else 1
    if n <= 1:
        return ""
    return (
        f"\nATTENTION : le contenu provient de {n} documents distincts (séparés par === SOURCE N ===). "
        "Synthétise et croise les informations de toutes les sources pour produire un cours cohérent.\n"
    )


def generate_slides(pdf_text: str, nb_slides: int = 5, nb_sources: int = 1) -> list[dict]:
    """
    Génère `nb_slides` slides depuis le texte extrait des PDFs.
    `nb_sources` permet d'adapter le prompt quand plusieurs fichiers ont été utilisés.
    """
    if not client:
        raise RuntimeError("OpenAI client non initialisé (OPENAI_API_KEY manquant ?)")

    source_note = (
        f"\nATTENTION : le contenu provient de {nb_sources} documents distincts "
        "(séparés par === SOURCE N ===). Synthétise et croise toutes les sources.\n"
        if nb_sources > 1 else ""
    )

    prompt = f"""Tu es un expert en formation professionnelle.
{source_note}
À partir du texte suivant, génère exactement {nb_slides} slides de présentation pédagogiques.
Réponds UNIQUEMENT avec un objet JSON contenant une clé "slides" dont la valeur est un tableau.
Chaque objet du tableau a :
- "order" (entier, commence à 1)
- "content" (contenu Markdown de la slide)

Règles de formatage Markdown OBLIGATOIRES pour chaque slide :
- Commence par un titre avec ## (titre principal de la slide)
- Utilise ### pour les sous-sections si nécessaire
- Utilise **texte** pour mettre en gras les notions clés
- Utilise des listes à puces (- item) pour énumérer des points
- Utilise *texte* pour l'italique si besoin de nuancer
- Chaque slide doit faire 5 à 10 lignes de contenu
- Ne jamais écrire du texte brut sans structure Markdown
- Ne pas utiliser de HTML
- Si plusieurs sources : assure-toi de couvrir chacune d'elles de façon équilibrée

Texte source :
---
{pdf_text}
---"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    data   = json.loads(response.choices[0].message.content)
    slides = data.get("slides", data) if isinstance(data, dict) else data
    return slides[:nb_slides]


def generate_questions(pdf_text: str, nb_questions: int = 5, nb_sources: int = 1) -> list[dict]:
    """
    Génère `nb_questions` QCM depuis le texte extrait des PDFs.
    `nb_sources` permet d'adapter le prompt quand plusieurs fichiers ont été utilisés.
    """
    if not client:
        raise RuntimeError("OpenAI client non initialisé (OPENAI_API_KEY manquant ?)")

    source_note = (
        f"\nATTENTION : le contenu provient de {nb_sources} documents distincts "
        "(séparés par === SOURCE N ===). Génère des questions couvrant toutes les sources.\n"
        if nb_sources > 1 else ""
    )

    prompt = f"""Tu es un expert en évaluation pédagogique.
{source_note}
À partir du texte suivant, génère exactement {nb_questions} questions à choix multiples (4 options).
Réponds UNIQUEMENT avec un objet JSON contenant une clé "questions" dont la valeur est un tableau.
Chaque objet du tableau a :
- "order" (entier)
- "text" (énoncé de la question)
- "choice_a", "choice_b", "choice_c", "choice_d" (texte de chaque option)
- "correct_answer" (lettre parmi "a", "b", "c", "d")
- "explanation" (justification courte de la bonne réponse)

Si plusieurs sources : assure-toi que les questions couvrent équitablement chacune d'elles.

Texte source :
---
{pdf_text}
---"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.5,
    )
    data      = json.loads(response.choices[0].message.content)
    questions = data.get("questions", data) if isinstance(data, dict) else data
    return questions[:nb_questions]
