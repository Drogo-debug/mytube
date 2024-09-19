from django.db import models

class Video(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='videos/')
    subtitle_file = models.FileField(upload_to='subtitles/', blank=True, null=True)  # English subtitle
    subtitle_file_fr = models.FileField(upload_to='subtitles_fr/', blank=True, null=True)
    subtitle_file_es = models.FileField(upload_to='subtitles_es/', blank=True, null=True)
    subtitle_file_hi = models.FileField(upload_to='subtitles_hi/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
