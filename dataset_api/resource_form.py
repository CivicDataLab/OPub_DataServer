from django import forms

from dataset_api.models import Resource


class CreateResourceMutationForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = [
            "title",
            "description",
            "file"
        ]
