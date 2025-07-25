from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 4}),
        }
