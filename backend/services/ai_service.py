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


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extrait le texte brut d'un PDF (bytes) via PyMuPDF."""
    import fitz  # PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def generate_slides(pdf_text: str, nb_slides: int = 5) -> list[dict]:
    """
    Génère `nb_slides` slides depuis le texte du PDF.
    Retourne une liste de dicts : [{"order": 1, "content": "..."}, ...]
    """
    if not client:
        raise RuntimeError("OpenAI client non initialisé (OPENAI_API_KEY manquant ?)")

    prompt = f"""Tu es un expert en formation professionnelle.
À partir du texte suivant, génère exactement {nb_slides} slides de présentation pédagogiques.
Réponds UNIQUEMENT avec un tableau JSON valide. Chaque objet a :
- "order" (entier, commence à 1)
- "content" (texte markdown de la slide, 3-6 lignes)

Texte source :
---
{pdf_text[:8000]}
---"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    data = json.loads(response.choices[0].message.content)
    # Normalise : GPT peut retourner {"slides": [...]} ou directement [...]
    slides = data.get("slides", data) if isinstance(data, dict) else data
    return slides[:nb_slides]


def generate_questions(pdf_text: str, nb_questions: int = 5) -> list[dict]:
    """
    Génère `nb_questions` QCM depuis le texte du PDF.
    Retourne une liste de dicts :
    [{"order": 1, "text": "...", "choice_a": "...", "choice_b": "...",
      "choice_c": "...", "choice_d": "...", "correct_answer": "a", "explanation": "..."}, ...]
    """
    if not client:
        raise RuntimeError("OpenAI client non initialisé (OPENAI_API_KEY manquant ?)")

    prompt = f"""Tu es un expert en évaluation pédagogique.
À partir du texte suivant, génère exactement {nb_questions} questions à choix multiples (4 options).
Réponds UNIQUEMENT avec un tableau JSON valide. Chaque objet a :
- "order" (entier)
- "text" (énoncé de la question)
- "choice_a", "choice_b", "choice_c", "choice_d" (texte de chaque option)
- "correct_answer" (lettre parmi "a", "b", "c", "d")
- "explanation" (justification courte de la bonne réponse)

Texte source :
---
{pdf_text[:8000]}
---"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.5,
    )
    data = json.loads(response.choices[0].message.content)
    questions = data.get("questions", data) if isinstance(data, dict) else data
    return questions[:nb_questions]
