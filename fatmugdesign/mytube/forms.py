from django import forms
from .models import Video

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title','file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',  # Styling for title field
                'placeholder': 'Enter video title',
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control-file',
            }),
        }
