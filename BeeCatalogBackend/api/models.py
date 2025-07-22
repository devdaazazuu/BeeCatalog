from django.db import models
from django.utils import timezone

class UploadedImage(models.Model):
    """
    Modelo para rastrear as URLs de imagens enviadas para o S3 e suas datas de expiração.
    """
    url = models.URLField(max_length=1024)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return self.url
