from django.db import models
from django.http import Http404
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
    needs_and_solutions_hub = ParentalKey(
        'NeedsAndSolutionsHub',
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

@register_setting(icon="help")
class NeedsAndSolutionsHub(BaseGenericSetting, ClusterableModel):

    panels = [
        InlinePanel('questions', label="Question", heading="Questions", min_num=1),
    ]

    class Meta:
        verbose_name = "Needs and solutions hub"


class NeedsAndSolutionsHubPage(Page):
    intro_text = RichTextField(
        blank=True,
        help_text="Introductory text shown before the wizard starts.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro_text"),
    ]

    subpage_types = []

    class Meta:
        verbose_name = "Needs & Solutions hub wizard page"

    def _build_wizard_form_list(self):
        questions = Question.objects.prefetch_related("options")

        form_list = []
        question_map = {}

        for question in questions:
            step_name = f"q_{question.pk}"
            form_class = make_question_form(question)
            form_list.append((step_name, form_class))
            question_map[step_name] = question

        return form_list, question_map

    def serve(self, request, *args, **kwargs):
        if getattr(request, "is_preview", False):
            return super().serve(request, *args, **kwargs)

        form_list, question_map = self._build_wizard_form_list()

        view = QuestionWizard.as_view(form_list=form_list)

        return view(
            request,
            wagtail_page=self,
            question_map=question_map,
        )

    @property
    def listing_title(self):
        return self.title




