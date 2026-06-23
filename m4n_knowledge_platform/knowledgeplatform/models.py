from typing import override
from django.core.paginator import Paginator
from django.conf import settings
from django.db import models
from django.db.models.functions import Coalesce
from django.db.models import Q

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from m4n_knowledge_platform.utils.blocks import CaptionedImageBlock
from m4n_knowledge_platform.utils.models import BasePage
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from ..news.models import ArticlePage, NewsListingPage
from ..utils.models import ArticleTopic, AuthorSnippet

from m4n_knowledge_platform.utils.templatetags.util_tags import table_of_contents_array, format_heading_id

class KnowledgeArticleTag(TaggedItemBase):
    content_object = ParentalKey(
            'knowledgeplatform.KnowledgeArticlePage',
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

@register_snippet
class KnowledgeArticleLicense(models.Model):
    title = models.CharField(blank=False, max_length=255)
    url = models.URLField(blank=False, null=False)
    slug = models.SlugField(blank=False, max_length=255)

    def __str__(self):
        return self.title

@register_snippet
class KnowledgeArticleFormat(models.Model):
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

class KnowledgeArticlePage(ArticlePage, ClusterableModel):

    template = "pages/knowledge_article_page.html"
    display_table_of_contents = models.BooleanField(default=True)

    authors = ParentalManyToManyField(
        'utils.AuthorSnippet',
        through='knowledgeplatform.Authorship',
        blank=True,
    )

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

    def filter_licence(self, request):
        return request.GET.get("licence")

    def filter_tag(self, request):
        return request.GET.getlist("tag")

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
        matching_license = self.filter_licence(request)
        matching_tags = self.filter_tag(request)

        queryset = self.apply_filters(base_queryset, topic=matching_topic, article_format=matching_format, article_license=matching_license, tags=matching_tags,
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

        # Paginate article pages
        paginator, page, _object_list, is_paginated = self.paginate_queryset(
            queryset, request
        )

        context["paginator"] = paginator
        context["paginator_page"] = page
        context["is_paginated"] = is_paginated

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

    search_fields = [] # We don't want the homepage to appear in search

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        InlinePanel(
            "page_related_pages",
            label="Featured articles for carousel",
            max_num=12,
        ),
    ]

    def get_topic_page_children(self):
        return self.get_children().type(KnowledgeHubTopicPage)

    def get_non_topic_page_children(self):
        return self.get_children().not_type(KnowledgeHubTopicPage)
