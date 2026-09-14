import re
from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import redirect
from formtools.wizard.storage import get_storage
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.models import ClusterableModel
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.models import Orderable, Page, TranslatableMixin
from wagtail.fields import RichTextField
from wagtail_localize.fields import TranslatableField, SynchronizedField

from ..knowledgeplatform.models import KnowledgeArticlePage

from .forms import make_question_form
from .wizard import QuestionWizard

class OptionTag(TaggedItemBase):
    content_object = ParentalKey(
        'Option',
        on_delete=models.CASCADE,
        related_name='tagged_items',
    )
class Option(TranslatableMixin, Orderable, ClusterableModel):
    question = ParentalKey(
        "Question",
        related_name="options",
        on_delete =models.CASCADE
    )
    text = RichTextField()

    tags = ClusterTaggableManager(through="OptionTag", blank=True)

    panels = [
        FieldPanel('text'),
        FieldPanel('tags'),
    ]

    translatable_fields = [TranslatableField("text"), SynchronizedField("tags")]

    class Meta(TranslatableMixin.Meta, Orderable.Meta):
        verbose_name = "Option"
        verbose_name_plural = "Options"

    def get_related_articles(self):
        return KnowledgeArticlePage.objects.filter(
            tags__in=self.tags.all()
        ).distinct()

    def clean(self):
        super().clean()
        # This goes inside a <label> tag and we strip paragraphs, so we should enforce that it's a single line of text.
        paragraph_count = len(re.findall(r'<p[ >]', self.text or ''))
        if paragraph_count > 1:
            raise ValidationError({
                'label': "This field only supports a single line, please remove the extra paragraph break(s)."
            })

    def save(self, *args, **kwargs):
        # wagtail_localize seems to have trouble tracking the locale in use all the way down
        # the page -> question -> option stack, leading to an integrity error on translating
        # or syncing. This ensures that the option always gets updated with its parent question's
        # locale, in order to avoid that.
        if self.question_id:
            question_locale_id = (
                Question.objects.filter(pk=self.question_id)
                .values_list("locale_id", flat=True)
                .first()
            )
            if question_locale_id and question_locale_id != self.locale_id:
                self.locale_id = question_locale_id
        self.locale = self.question.locale
        super().save(*args, **kwargs)


class Question(TranslatableMixin, Orderable, ClusterableModel):
    page = ParentalKey(
        'NeedsAndSolutionsHubSurveyPage',
        on_delete=models.CASCADE,
        related_name='questions',
    )
    text = models.TextField()
    intro_text = RichTextField(blank=True, null=True, help_text="Short descriptive text putting the questoin in context, and if relevant, summarising the previous questions asked.")
    why_relevant_explanation = RichTextField(blank=True, null=True, help_text="Optional short text explaining why this question is relevant, shown at the bottom of the page.")

    panels = [
        FieldPanel('text'),
        FieldPanel("intro_text"),
        FieldPanel("why_relevant_explanation"),
        InlinePanel('options', label="Option", heading="Options", min_num=2),
    ]

    translatable_fields = [
        TranslatableField('text'),
        TranslatableField('intro_text'),
        TranslatableField('why_relevant_explanation'),
        TranslatableField('options'),
    ]

    class Meta(TranslatableMixin.Meta, Orderable.Meta):
        verbose_name = "Question"
        verbose_name_plural = "Questions"


class NeedsAndSolutionsHubIndexPage(Page):

    template = "needs_and_solutions_hub/index.html"

    subpage_types = [
        "needs_and_solutions_hub.NeedsAndSolutionsHubFilterPage",
        "needs_and_solutions_hub.NeedsAndSolutionsHubSurveyPage"
    ]

    color_hex = models.CharField(null=True,
        blank=True,
        max_length=10,
        help_text="The background color for the CTA to this page on the homepage, expressed as any valid css colour string (eg #ff0000 or rgb(1, 2, 3))"
    )

    introduction = RichTextField(
        blank=True,
        help_text="Description of purpose used on the homepage CTA"
    )

    intro_text = RichTextField(
        blank=True,
        help_text="Introductory text shown above the grid of needs.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("intro_text"),
        FieldPanel("color_hex"),
    ]

    translatable_fields = [
        TranslatableField('introduction'),
        TranslatableField('intro_text'),
        SynchronizedField('color_hex'),
        TranslatableField('title'),
    ]


class FilterPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'NeedsAndSolutionsHubFilterPage',
        on_delete=models.CASCADE,
        related_name='tagged_items',
    )

class NeedsAndSolutionsHubFilterPage(Page):
    template = "needs_and_solutions_hub/wizard_result.html"

    tags = ClusterTaggableManager(through="FilterPageTag", blank=True)
    need_description = RichTextField(blank=True, help_text="The need shown in the grid on the needs and solutions hub index page")
    results_explanation = RichTextField(blank=True, help_text="The explanatory paragraph shown above the results on the final page.")

    subpage_types = []

    parent_page_types = ["needs_and_solutions_hub.NeedsAndSolutionsHubIndexPage"]

    translatable_fields = [
        TranslatableField('title'),
        TranslatableField('need_description'),
        TranslatableField('results_explanation'),
        SynchronizedField('tags'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("need_description"),
        FieldPanel('results_explanation'),
        FieldPanel('tags'),
    ]

    @property
    def show_start_again(self):
        return False


    def get_related_articles(self):
        return KnowledgeArticlePage.objects.filter(
            tags__in=self.tags.all()
        ).annotate(
            common_tags=models.Count(
                'tags',
                filter=models.Q(tags__in=self.tags.all()),
                distinct=True
            )
        ).order_by('-common_tags')


    def compute_result(self):
        return { "tags": self.tags, "articles": self.get_related_articles() }


    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["page"] = self
        context["result"] = self.compute_result()
        return context

class NeedsAndSolutionsHubSurveyPage(Page, ClusterableModel):
    need_description = RichTextField(blank=True, help_text="The need shown in the grid on the needs and solutions hub index page")

    results_explanation = RichTextField(blank=True, help_text="The explanatory paragraph shown above the results on the final page.")

    content_panels = Page.content_panels + [
        FieldPanel('need_description'),
        FieldPanel("results_explanation"),
        InlinePanel('questions', label="Question", heading="Questions", min_num=1),
    ]

    translatable_fields = [
        TranslatableField('title'),
        TranslatableField('need_description'),
        TranslatableField('results_explanation'),
        SynchronizedField('slug'),
        TranslatableField('questions'),
    ]

    subpage_types = []
    parent_page_types = ["needs_and_solutions_hub.NeedsAndSolutionsHubIndexPage"]

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
                    .filter(page=self.pk)
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
    def show_start_again(self):
        return True

    @property
    def listing_title(self):
        return self.title




