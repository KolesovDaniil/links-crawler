from django.views.generic.edit import FormView
from django.forms import Form
from django.shortcuts import render
from .utils import get_page_links

from .forms import PageUrlsForm


class LinksOnPageView(FormView):
    template_name = 'homepage.html'
    form_class = PageUrlsForm

    def form_valid(self, form: Form):
        page_url = form.changed_data['url']
        extra = {'found_links': get_page_links(page_url)}

        return render(
            self.request, self.template_name, context=self.get_context_data() | extra
        )

    def _get_urls_for_page(self, page_url: str) -> list[str]:
        """Return all urls on page including nested urls"""
        pass

