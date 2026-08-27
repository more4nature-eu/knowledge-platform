import json
from typing import override
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.conf import settings
from django.db import models
from django.db.models.functions import Coalesce
from django.db.models import Q
from django.template.defaultfilters import slugify

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, TabbedInterface, ObjectList
from wagtail.fields import RichTextField, StreamField
from wagtail.snippets.blocks import SnippetChooserBlock
from m4n_knowledge_platform.utils.blocks import CaptionedImageBlock
from m4n_knowledge_platform.utils.models import BasePage
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page, TranslatableMixin
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtailterms.models import Term
from wagtailgeowidget import geocoders
from wagtailgeowidget.helpers import geosgeometry_str_to_struct
from wagtailgeowidget.panels import GeoAddressPanel, LeafletPanel

from ..news.models import ArticlePage, NewsListingPage
from ..utils.models import ArticleTopic, AuthorSnippet, ContactSnippet, CaseScopeSnippet

from m4n_knowledge_platform.utils.templatetags.util_tags import table_of_contents_array, format_heading_id

class KnowledgeArticleTag(TaggedItemBase):
    content_object = ParentalKey(
            'knowledgeplatform.KnowledgeArticlePage',
            on_delete=models.CASCADE, related_name='tagged_items'
    )

class KnowledgeCaseTag(TaggedItemBase):
    content_object = ParentalKey(
            'knowledgeplatform.KnowledgeHubCasePage',
            on_delete=models.CASCADE, related_name='tagged_items'
    )

class KnowledgeArticleAttachedResource(models.Model):
    title = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=True)
    url = models.URLField(blank=False, null=False)

    page = ParentalKey(
        'knowledgeplatform.KnowledgeArticlePage',
        on_delete=models.PROTECT,
        related_name='attached_resources'
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
        FieldPanel("url"),
    ]

class KnowledgeCaseAttachedResource(models.Model):
    title = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=True)
    url = models.URLField(blank=False, null=False)

    page = ParentalKey(
        'knowledgeplatform.KnowledgeHubCasePage',
        on_delete=models.PROTECT,
        related_name='attached_resources'
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
        FieldPanel("url"),
    ]

class KnowledgeCaseAttachedDataset(models.Model):
    title = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=True)
    url = models.URLField(blank=False, null=False)
    source = models.TextField(blank=True)

    page = ParentalKey(
        'knowledgeplatform.KnowledgeHubCasePage',
        on_delete=models.PROTECT,
        related_name='attached_datasets'
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
        FieldPanel("url"),
        FieldPanel("source",
            heading="Source (API, report, dataset)"),
    ]

STAKEHOLDER_CHOICES = [
    ("authority", "Authority"),
    ("citizen-science-initiative", "Citizen Science Initiative"),
    ("undefined", "Undefined"),
]


class KnowledgeCaseStakeholder(models.Model):
    title = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    stakeholder_type = models.CharField(
        max_length=255,
        choices=STAKEHOLDER_CHOICES,
        default="undefined"
    )

    page = ParentalKey(
        'knowledgeplatform.KnowledgeHubCasePage',
        on_delete=models.PROTECT,
        related_name='stakeholders'
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
        FieldPanel("url"),
        FieldPanel("stakeholder_type",
            heading="Stakeholders"),
    ]

    def __str__(self):
        return self.title

@register_snippet
class KnowledgeArticleLicense(models.Model):
    title = models.CharField(blank=False, max_length=255)
    url = models.URLField(blank=False, null=False)
    slug = models.SlugField(blank=False, max_length=255)

    def __str__(self):
        return self.title

@register_snippet
class KnowledgeArticleFormat(TranslatableMixin, models.Model):
    title = models.CharField(blank=False, max_length=255)
    description = models.CharField(blank=False, max_length=225)
    slug = models.SlugField(blank=False, max_length=255)

    def __str__(self):
        return self.title

class Authorship(Orderable):
    page = ParentalKey(
        'knowledgeplatform.KnowledgeArticlePage',
        on_delete=models.CASCADE,
        related_name='authorships',
    )
    author = models.ForeignKey(
        'utils.AuthorSnippet',
        on_delete=models.CASCADE,
        related_name='authorships',
    )

    panels = [
        FieldPanel('author'),
    ]

    def __str__(self):
        return self.author.title

class CaseContact(Orderable):
    page = ParentalKey(
        'knowledgeplatform.KnowledgeHubCasePage',
        on_delete=models.CASCADE,
        related_name='contacts',
    )
    contact = models.ForeignKey(
        'utils.ContactSnippet',
        on_delete=models.CASCADE,
        related_name='contacts',
    )

    panels = [
        FieldPanel('contact'),
    ]

    def __str__(self):
        return self.contact.title

class KnowledgeArticlePage(ArticlePage, ClusterableModel):

    template = "pages/knowledge_article_page.html"
    display_table_of_contents = models.BooleanField(default=True)

    parent_page_types = ["knowledgeplatform.KnowledgeHubListingPage"]

    tags = ClusterTaggableManager(through=KnowledgeArticleTag, blank=True)

    search_keywords = models.TextField(blank=True)

    article_format = models.ForeignKey(
        "knowledgeplatform.KnowledgeArticleFormat",
        blank=True,
        null=True,
        on_delete=models.deletion.PROTECT,
        related_name="pages",
    )

    article_license = models.ForeignKey(
        "knowledgeplatform.KnowledgeArticleLicense",
        blank=True,
        null=True,
        on_delete=models.deletion.PROTECT,
        related_name="pages",
    )


    promote_panels = ArticlePage.promote_panels + [
        FieldPanel("search_keywords"),
    ]

    content_panels = ArticlePage.content_panels[0:1] + [
        InlinePanel("authorships", label="Authors")
    ] + ArticlePage.content_panels[2:-1] + [
        FieldPanel("display_table_of_contents"),
        InlinePanel("attached_resources"),
        FieldPanel("article_format"),
        FieldPanel("article_license"),
        FieldPanel('tags'),
        InlinePanel("footnotes", label="Footnotes"),
        MultiFieldPanel(
            [
                InlinePanel(
                    "page_related_pages",
                    label="Pages",
                ),
            ],
            heading="Related pages",
        ),
    ]

    search_fields = ArticlePage.search_fields + [
        index.SearchField("search_keywords"),
        index.SearchField("body"),
        index.SearchField("introduction"),
        index.SearchField("title"),
    ]

    def full_clean(self, *args, **kwargs):
        # We don't use the singular "author" association, but it's defined as non-null
        # on the superclass, so we default it to something sensible here.
        if not self.author_id:
                self.author = AuthorSnippet.objects.get_or_create(title="more4nature")[0]
        super().full_clean(*args, **kwargs)

    @property
    def table_of_contents(self):
        return table_of_contents_array(self.body)

    @property
    def page_authors(self):
        return Authorship.objects.filter(page_id=self.pk)

    @property
    def page_attached_resources(self):
        return KnowledgeArticleAttachedResource.objects.filter(page_id=self.pk)

    @property
    def has_real_translations(self):
        return (
            self.get_translations()
            .live()
            .filter(alias_of__isnull=True)
            .exists()
        )

    @property
    def topic_page(self):
        return (
            KnowledgeHubTopicPage.objects
            .live()
            .public()
            .filter(topic_id=self.topic.id)
            .filter(locale=self.locale)
        )

class FilterableListingMixin:

    def paginate_queryset(self, queryset, request):
        """Paginate the queryset."""
        page_number = request.GET.get("page", 1)
        paginator = Paginator(queryset, settings.DEFAULT_PER_PAGE)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return (paginator, page, page.object_list, page.has_other_pages())

    def base_queryset(self):
        return KnowledgeArticlePage.objects.child_of(self)

    def filter_topic(self, request):
        return request.GET.get("topic")

    def filter_format(self, request):
        return request.GET.get("format")

    def filter_license(self, request):
        return request.GET.get("license")

    def filter_tag(self, request):
        return request.GET.getlist("tag")

    def search_query(self, request):
        return request.GET.get("query")

    def topic_filter_visible(self):
        return True

    def format_filter_visible(self):
        return True

    def licence_filter_visible(self):
        return True

    def tag_filter_visible(self):
        return True

    def apply_filters(self, queryset, topic=None, article_format=None, article_license=None, tags=None):
        """
        Apply any combination of article filters to a queryset.
        """

        if topic:
            queryset = queryset.filter(topic__slug=topic)

        if article_format:
            queryset = queryset.filter(
                article_format__slug=article_format
            )

        if article_license:
            queryset = queryset.filter(
                article_license__slug=article_license
            )

        if tags:
            #AND option (discarded)
            for tag in tags:
                queryset = queryset.filter(tags__slug=tag)

            # OR option
            #tag_query = Q()

            #for tag in tags:
            #    tag_query |= Q(tags__slug=tag)
            # queryset = queryset.filter(tag_query)

        return queryset.distinct()

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        base_queryset = (
            self.base_queryset()
                .live()
                .public()
                .annotate(
                    date=Coalesce("publication_date", "first_published_at"),
                )
                .select_related(
                    "author",
                    "topic",
                    "article_format",
                    "article_license"
                )
                .prefetch_related("tags")
                .order_by("-date")
        )

        # Get url parameters
        matching_topic = self.filter_topic(request)
        matching_format = self.filter_format(request)
        matching_license = self.filter_license(request)
        matching_tags = self.filter_tag(request)
        search_query = self.search_query(request)

        queryset = self.apply_filters(base_queryset,
            topic=matching_topic,
            article_format=matching_format,
            article_license=matching_license,
            tags=matching_tags,
        )

        topic_queryset = self.apply_filters(
            base_queryset,
            article_format=matching_format,
            article_license=matching_license,
            tags=matching_tags,
        )

        format_queryset = self.apply_filters(
            base_queryset,
            topic=matching_topic,
            article_license=matching_license,
            tags=matching_tags,
        )

        license_queryset = self.apply_filters(
            base_queryset,
            topic=matching_topic,
            article_format=matching_format,
            tags=matching_tags,
        )

        tag_queryset = self.apply_filters(
            base_queryset,
            topic=matching_topic,
            article_format=matching_format,
            article_license=matching_license
        )

        article_topics = (
            ArticleTopic.objects.filter(
                article_pages__in=topic_queryset
            )
            .values("title", "slug")
            .distinct()
            .order_by("title")
        )

        article_formats = (
            KnowledgeArticleFormat.objects.filter(
                pages__in=format_queryset
            )
            .values("title", "slug")
            .distinct()
            .order_by("title")
        )

        article_licenses = (
            KnowledgeArticleLicense.objects.filter(
                pages__in=license_queryset
            )
            .values("title", "slug")
            .distinct()
            .order_by("title")
        )

        tag_ids = (
            KnowledgeArticleTag.objects.filter(
                content_object__in=tag_queryset
            )
            .values("tag")
            .distinct()
            .order_by("tag")
        )

        tags = KnowledgeArticleTag.objects.filter(tag_id__in=tag_ids).order_by("tag")

        # Topics
        context["topics"] = article_topics
        context["matching_topic"] = matching_topic

        # Format
        context["formats"] = article_formats
        context["matching_format"] = matching_format

        # License
        context["licenses"] = article_licenses
        context["matching_license"] = matching_license

        # Tags
        context["tags"] = tags
        context["matching_tags"] = matching_tags

        # Search filter
        if search_query:
            # The only way "possible" to avoid adding all filters to searchable fields
            queryset = KnowledgeArticlePage.objects.filter(
                pk__in=queryset.values("pk")
            ).search(search_query)

            context["search_query"] = search_query
            context["search_results"] = queryset
            context["SEO_NOINDEX"] = bool(search_query)  # prevent google from indexing

        # Paginate article pages
        paginator, page, _object_list, is_paginated = self.paginate_queryset(
            queryset, request
        )

        context["paginator"] = paginator
        context["paginator_page"] = page
        context["is_paginated"] = is_paginated

        return context

class KnowledgeHubListingPage(FilterableListingMixin, NewsListingPage):

    template = "pages/knowledge_listing_page.html"

    subpage_types = ["knowledgeplatform.KnowledgeArticlePage"]
    max_count = None

    image = StreamField(
        [("image", CaptionedImageBlock())],
        blank=True,
        max_num=1,
    )

    color_hex = models.CharField(null=True,
        blank=True,
        max_length=10,
        help_text="The background color for the CTA to this page on the homepage, expressed as any valid css colour string (eg #ff0000 or rgb(1, 2, 3))")

    content_panels = (
        NewsListingPage.content_panels
        + [
            FieldPanel("image"),
            FieldPanel("color_hex"),
        ]
    )

    @property
    def text_color(self):
        if self.color_hex is None: return "#ffffff"
        hex_color = self.color_hex.lstrip("#")

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # Perceived luminance
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

        return "#ffffff" if luminance < 140 else "#243B4A"

class KnowledgeHubTopicPage(FilterableListingMixin, Page):

    template = "pages/knowledge_listing_page.html"

    topic = models.ForeignKey(
            ArticleTopic,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name="topic_page",
        )

    content_panels = Page.content_panels + [
        FieldPanel("topic"),
    ]

    @override
    def base_queryset(self):
        return KnowledgeArticlePage.objects

    @override
    def filter_topic(self, request):
        return self.topic.slug

    @override
    def topic_filter_visible(self):
        return False

    @property
    def articles(self):
        return KnowledgeArticlePage.objects.live().public().filter(topic=self.topic)

class KnowledgeHubHomePage(BasePage):
    template = "pages/knowledge_home_page.html"
    introduction = RichTextField(blank=True)

    working_with_title = models.CharField(max_length=255, blank=True)
    working_with_statistics = StreamField(
        [("statistic", SnippetChooserBlock("utils.Statistic"))],
        blank=True,
        max_num=4,
    )

    search_fields = [] # We don't want the homepage to appear in search

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        InlinePanel(
            "page_related_pages",
            label="Featured articles for carousel",
            max_num=12,
        ),
        MultiFieldPanel(
            [
                FieldPanel("working_with_title", heading="Title"),
                FieldPanel("working_with_statistics", heading="Additional statistics"),
            ],
            heading="Who we are working with section",
        ),
    ]

    def get_topic_page_children(self):
        return self.get_children().type(KnowledgeHubTopicPage).live()

    def get_case_listing_children(self):
        return self.get_children().type(KnowledgeHubCaseListingPage).live()

    def get_case_listing_page(self):
        return self.get_case_listing_children().first()

    def get_cases_count(self):
        case_listing_page = self.get_case_listing_page()
        if not case_listing_page:
            return 0
        return KnowledgeHubCasePage.objects.child_of(case_listing_page).live().public().count()

    def get_featured_children(self):
        from m4n_knowledge_platform.needs_and_solutions_hub.models import NeedsAndSolutionsHubPage # Avoid circular import

        return self.get_children().type(KnowledgeHubListingPage, NeedsAndSolutionsHubPage).live()

class KnowledgeHubGlossaryPage(BasePage):
    template = "pages/knowledge_glossary_page.html"

    introduction = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("introduction")
    ]

    def get_terms(self):
        return Term.objects.all()

    @property
    def table_of_contents(self):
        h2_terms = [(term.term,
            slugify(term.term))
            for term in self.get_terms()]

        return h2_terms

class KnowledgeHubSearchPage(FilterableListingMixin, BasePage):
    template = "pages/search_view.html"

    @override
    def base_queryset(self):
        return KnowledgeArticlePage.objects.live().filter(
            locale=self.locale)

class KnowledgeHubCasePage(ArticlePage, ClusterableModel):

    template = "pages/knowledge_case_page.html"
    display_table_of_contents = models.BooleanField(default=True)
    display_date = models.BooleanField(default=False)

    scope = models.ForeignKey(
        "utils.CaseScopeSnippet",
        on_delete=models.deletion.PROTECT,
        related_name="cases",
    )

    cgd_intro = RichTextField(
        blank=True, features=["bold", "italic", "link"]
    )

    location = models.CharField(max_length=250, blank=True, null=True)
    location_label = models.CharField(
        max_length=255,
        blank=True,
        help_text="Place name. Used both to search/geocode the pin on the map and shown publicly on the page",
    )
    location_zoom = models.SmallIntegerField(blank=True, null=True, default=9)

    parent_page_types = ["knowledgeplatform.KnowledgeHubCaseListingPage"]

    tags = ClusterTaggableManager(through=KnowledgeCaseTag, blank=True)

    search_keywords = models.TextField(blank=True)

    promote_panels = ArticlePage.promote_panels + [
        FieldPanel('tags')
    ]
    settings_panels = ArticlePage.settings_panels + [
        FieldPanel("search_keywords"),
        MultiFieldPanel(
            [
                FieldPanel("display_date"),
                FieldPanel("display_table_of_contents"),
            ],
            heading="Display options",
        ),
    ]

    content_panels = ArticlePage.content_panels[0:1] +\
        ArticlePage.content_panels[4:-1] + [
        InlinePanel("footnotes", label="Footnotes"),
        MultiFieldPanel(
            [
                InlinePanel(
                    "page_related_pages",
                    label="Pages",
                ),
            ],
            heading="Related pages (in the knowledge platform)",
        ),
    ]

    # Custom list of panels. We'll put this in an ObjectList later.
    metadata_panels = [
        ArticlePage.content_panels[3],
        FieldPanel("scope"),
        InlinePanel("contacts", label="Contacts"),
        MultiFieldPanel(
            [
                InlinePanel(
                    "attached_resources",
                    label="Attachments",
                ),
            ],
            heading="Attached resources",
            help_text="Press coverage, academic articles, etc."
        ),
        MultiFieldPanel(
            [
                InlinePanel(
                    "stakeholders",
                    label="Stakeholders",
                ),
            ],
            heading="Case stakeholders",
        ),
        MultiFieldPanel(
            [
                FieldPanel("cgd_intro", heading="CGD introductory text"),
                InlinePanel("attached_datasets"),
            ],
            heading="Citizen Generated Data",
        ),
        MultiFieldPanel(
            [
                GeoAddressPanel("location_label", geocoder=geocoders.NOMINATIM),
                LeafletPanel("location", address_field="location_label", zoom_field="location_zoom"),
            ],
            heading="Location",
        )
    ]

    # This is where all the tabs are created
    edit_handler = TabbedInterface(
        [
            ObjectList(content_panels, heading='Content'),
            # This is our custom banner_panels. It's just a list, how easy!
            ObjectList(metadata_panels, heading="Case Metadata"),
            ObjectList(promote_panels, heading='Promote'),
            ObjectList(settings_panels, heading='Settings'),
        ]
    )

    search_fields = ArticlePage.search_fields + [
        index.SearchField("search_keywords"),
        index.SearchField("body"),
        index.SearchField("introduction"),
        index.SearchField("title"),
        index.SearchField("cgd_intro")
    ]

    def full_clean(self, *args, **kwargs):
        # We don't use the singular "author" association, but it's defined as non-null
        # on the superclass, so we default it to something sensible here.
        if not self.author_id:
                self.author = AuthorSnippet.objects.get_or_create(title="more4nature")[0]
        super().full_clean(*args, **kwargs)

    @property
    def table_of_contents(self):
        return table_of_contents_array(self.body)

    @property
    def location_struct(self):
        if not self.location:
            return None
        return geosgeometry_str_to_struct(self.location)

    @property
    def page_contacts(self):
        return CaseContact.objects.filter(page_id=self.pk)

    @property
    def page_attached_resources(self):
        return KnowledgeCaseAttachedResource.objects.filter(page_id=self.pk)

    @property
    def page_attached_datasets(self):
        return KnowledgeCaseAttachedDataset.objects.filter(page_id=self.pk)

    @property
    def page_stakeholders(self):
        return KnowledgeCaseStakeholder.objects.filter(page_id=self.pk)

    @property
    def has_real_translations(self):
        return (
            self.get_translations()
            .live()
            .filter(alias_of__isnull=True)
            .exists()
        )

    # TODO - Do we want this to be linked too
    @property
    def topic_page(self):
        return (
            KnowledgeHubTopicPage.objects
            .live()
            .public()
            .filter(topic_id=self.topic.id)
            .filter(locale=self.locale)
        )

class KnowledgeHubCaseListingPage(NewsListingPage):

    template = "pages/knowledge_case_listing_page.html"

    subpage_types = ["knowledgeplatform.KnowledgeHubCasePage"]
    max_count = None

    image = StreamField(
        [("image", CaptionedImageBlock())],
        blank=True,
        max_num=1,
    )

    content_panels = (
        NewsListingPage.content_panels
        + [
            FieldPanel("image"),
        ]
    )

    def paginate_queryset(self, queryset, request):
        """Paginate the queryset."""
        page_number = request.GET.get("page", 1)
        paginator = Paginator(queryset, settings.DEFAULT_PER_PAGE)
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return (paginator, page, page.object_list, page.has_other_pages())

    def get_context(self, request, *args, **kwargs):
        # Skip NewsListingPage.get_context, which is hardcoded to query ArticlePage.
        context = super(NewsListingPage, self).get_context(request, *args, **kwargs)

        base_queryset = (
            KnowledgeHubCasePage.objects.child_of(self)
            .live()
            .public()
            .filter(locale=self.locale)
            .select_related("scope", "topic")
            .order_by("title")
        )

        matching_scope = request.GET.get("scope")
        queryset = base_queryset
        if matching_scope:
            queryset = queryset.filter(scope__slug=matching_scope)

        scopes = (
            CaseScopeSnippet.objects.filter(cases__in=base_queryset)
            .values("title", "slug")
            .distinct()
            .order_by("title")
        )

        cases_geojson = []
        for case in queryset:
            location_struct = case.location_struct
            if not location_struct:
                continue
            cases_geojson.append({
                "id": case.id,
                "title": case.title,
                "url": case.url,
                "lat": float(location_struct["y"]),
                "lng": float(location_struct["x"]),
                "location_label": case.location_label,
                "scope": case.scope.title if case.scope_id else None,
                "topic": {
                    "title": case.topic.title,
                    "color": case.topic.color_hex,
                } if case.topic_id else None,
            })

        paginator, page, _object_list, is_paginated = self.paginate_queryset(
            queryset, request
        )

        context["cases"] = page
        context["paginator"] = paginator
        context["paginator_page"] = page
        context["is_paginated"] = is_paginated
        context["cases_geojson"] = json.dumps(cases_geojson)
        context["scopes"] = scopes
        context["matching_scope"] = matching_scope

        return context
