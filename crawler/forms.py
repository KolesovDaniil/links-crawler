from django import forms


class PageUrlsForm(forms.Form):
    url = forms.URLField(
        label="URL",
        widget=forms.TextInput(
            attrs={"placeholder": "https://your-url.com", "class": "u-full-width"}
        ),
    )
