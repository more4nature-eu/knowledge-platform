from django.db import models
from django.http import Http404
from django.shortcuts import redirect
from formtools.wizard.storage import get_storage
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.models import Orderable, Page
from wagtail.fields import RichTextField

from .forms import make_question_form
from .wizard import QuestionWizard

class Option(Orderable):
    question = ParentalKey(
        "Question",
        related_name="options",
        on_delete =models.CASCADE
    )
    text = models.TextField()

    panels = [
        FieldPanel('text'),
    ]

    class Meta:
        verbose_name = "Option"
        verbose_name_plural = "Options"

class Question(Orderable, ClusterableModel):
    page = ParentalKey(
        'NeedsAndSolutionsHubPage',
        on_delete=models.CASCADE,
        related_name='questions',
    )
    text = models.TextField()

    panels = [
        FieldPanel('text'),
        InlinePanel('options', label="Option", heading="Options", min_num=2),
    ]
    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"

class NeedsAndSolutionsHubPage(Page, ClusterableModel):
    intro_text = RichTextField(
        blank=True,
        help_text="Introductory text shown before the wizard starts.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro_text"),
        InlinePanel('questions', label="Question", heading="Questions", min_num=1),
    ]

    subpage_types = []

    class Meta:
        verbose_name = "Needs & Solutions hub wizard page"

    def _build_wizard_form_list(self, pks):
        questions_by_pk = {
            q.pk: q
            for q in Question.objects
                .filter(pk__in=pks)
                .prefetch_related("options")
        }

        form_list = []
        question_map = {}

        for pk in pks:
            question = questions_by_pk.get(pk)
            if question is None:
                continue
            step_name = f"q_{pk}"
            form_class = make_question_form(question)
            form_list.append((step_name, form_class))
            question_map[step_name] = question

        return form_list, question_map


    def serve(self, request, *args, **kwargs):
        if getattr(request, "is_preview", False):
            return super().serve(request, *args, **kwargs)

        session_key = f"wizard_questions_{self.pk}"

        wizard_prefix = QuestionWizard.__name__.lower()

        is_fresh_start = (
            request.method == "GET"
            or wizard_prefix + "-current_step" not in request.POST
        )

        if is_fresh_start:
            pks = list(
                Question.objects
                    .order_by("sort_order")
                    .values_list("pk", flat=True)
            )
            request.session[session_key] = pks
            storage = get_storage(
                "formtools.wizard.storage.session.SessionStorage",
                wizard_prefix,
                request,
                None,
            )
            storage.reset()
        else:
            pks = request.session.get(session_key)

        if pks is None:
            return redirect(self.url)

        form_list, question_map = self._build_wizard_form_list(pks)

        view = QuestionWizard.as_view(form_list=form_list)
        return view(request, wagtail_page=self, question_map=question_map)

    @property
    def listing_title(self):
        return self.title




