from django.db import models
from django.db.models.functions import Coalesce
from django.db.models import Q
from urllib.parse import urlencode

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import StreamField
from m4n_knowledge_platform.utils.blocks import CaptionedImageBlock
from wagtail.models import Orderable
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

class KnowledgeHubListingPage(NewsListingPage):

    template = "pages/knowledge_listing_page.html"

    subpage_types = ["knowledgeplatform.KnowledgeArticlePage"]
    max_count = None

    image = StreamField(
        [("image", CaptionedImageBlock())],
        blank=True,
        max_num=1,
    )

    color_hex = models.CharField(null=True, blank=True, max_length=10)

    content_panels = (
        NewsListingPage.content_panels
        + [
            FieldPanel("image"),
            FieldPanel("color_hex"),
        ]
    )

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
            # AND option (discarded)
            # for tag in tags:
            #     queryset = queryset.filter(tags__slug=tag)

            # OR option
            tag_query = Q()

            for tag in tags:
                tag_query |= Q(tags__slug=tag)

            queryset = queryset.filter(tag_query)

        return queryset.distinct()

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        base_queryset = (
            KnowledgeArticlePage.objects.live()
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
            .child_of(self)
        )

        # Get url parameters
        matching_topic = request.GET.get("topic")
        matching_format = request.GET.get("format")
        matching_license = request.GET.get("license")
        matching_tags = request.GET.getlist("tag")

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
