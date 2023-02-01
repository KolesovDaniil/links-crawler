from django import forms


class PageUrlsForm(forms.Form):
    url = forms.URLField()
