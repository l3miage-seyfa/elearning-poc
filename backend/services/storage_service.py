"""
Storage Service — upload/download de fichiers PDF vers Railway Storage Bucket (S3-compatible).
"""
import boto3
from django.conf import settings


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )


def upload_pdf(file_bytes: bytes, filename: str) -> str:
    """
    Upload un PDF dans le bucket Railway.
    Retourne la clé S3 (chemin dans le bucket).
    """
    client = _get_s3_client()
    key = f"courses/pdfs/{filename}"
    client.put_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType="application/pdf",
    )
    return key


def get_pdf_url(key: str, expires_in: int = 3600) -> str:
    """Génère une URL présignée pour télécharger le PDF (valide `expires_in` secondes)."""
    client = _get_s3_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
        ExpiresIn=expires_in,
    )
