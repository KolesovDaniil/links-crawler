from typing import Any

from django.forms import Form
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic.edit import FormView

from .forms import PageUrlsForm
from .utils import LinksCrawler, render_html_links_tree


class LinksOnPageView(FormView):
    template_name = "homepage.html"
    form_class = PageUrlsForm

    def form_valid(self, form: Form) -> HttpResponse:
        page_url = form.cleaned_data["url"]
        crawler = LinksCrawler(page_url)

        links_tree_exists, tree = crawler.get_links()

        if links_tree_exists:
            tree = render_html_links_tree(tree)

        extra = {"links_tree_exists": links_tree_exists, "links_tree": tree}

        return render(
            self.request, self.template_name, context=self.get_context_data() | extra
        )

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpRequest:
        return self.render_to_response(
            self.get_context_data() | {"initial_state": True}
        )
