from django.conf import settings
from django.db import models
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from wagtail.admin.panels import FieldPanel, HelpPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.search import index

from wagtail.fields import StreamField
from m4n_knowledge_platform.utils.models import BasePage, ArticleTopic, ArticleType
from m4n_knowledge_platform.utils.blocks import CaptionedImageBlock, StoryBlock, FeaturedArticleBlock
from m4n_knowledge_platform.utils.templatetags.util_tags import table_of_contents_array, format_heading_id

class ArticlePage(BasePage):
    template = "pages/article_page.html"
    parent_page_types = ["news.NewsListingPage"]
    display_table_of_contents = models.BooleanField(default=True)

    author = models.ForeignKey(
        "utils.AuthorSnippet",
        blank=False,
        null=False,
        on_delete=models.deletion.PROTECT,
        related_name="+",
    )
    topic = models.ForeignKey(
        "utils.ArticleTopic",
        blank=False,
        null=False,
        on_delete=models.deletion.PROTECT,
        related_name="article_pages",
    )
    type = models.ForeignKey(
        "utils.ArticleType",
        blank=False,
        null=True,
        on_delete=models.deletion.PROTECT,
        related_name="article_types",
    )
    publication_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Use this field to override the date that the "
        "news item appears to have been published.",
    )
    introduction = models.TextField(blank=True)
    image = StreamField(
        [("image", CaptionedImageBlock())],
        blank=True,
        max_num=1,
    )
    body = StreamField(StoryBlock())
    featured_section_title = models.TextField(blank=True)

    search_fields = BasePage.search_fields + [
        index.SearchField("introduction"),
        index.FilterField("topic"),
        index.FilterField("type"),

    ]

    content_panels = BasePage.content_panels + [
        FieldPanel("author"),
        FieldPanel("publication_date"),
        FieldPanel("display_table_of_contents"),
        FieldPanel("topic"),
        FieldPanel("type"),
        FieldPanel("introduction"),
        FieldPanel("image"),
        FieldPanel("body"),
        MultiFieldPanel(
            [
                FieldPanel("featured_section_title", heading="Title"),
                InlinePanel(
                    "page_related_pages",
                    label="Pages",
                    max_num=3,
                ),
            ],
            heading="Featured section",
        ),
    ]

    @property
    def display_date(self):
        if self.publication_date:
            return self.publication_date.strftime("%d %b %Y")
        elif self.first_published_at:
            return self.first_published_at.strftime("%d %b %Y")

    @property
    def table_of_contents(self):
        return table_of_contents_array(self.body)

class NewsListingPage(BasePage):
    template = "pages/news_listing_page.html"
    subpage_types = ["news.ArticlePage"]
    max_count = 1  # Allow only one news listing page to keep article pages in one place

    introduction = RichTextField(
        blank=True, features=["bold", "italic", "link"]
    )

    search_fields = BasePage.search_fields + [index.SearchField("introduction")]

    content_panels = (
        BasePage.content_panels
        + [
            FieldPanel("introduction"),
            # FieldPanel("featured_card"),
            HelpPanel("This page will automatically display child Article pages."),
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
        context = super().get_context(request, *args, **kwargs)
        queryset = (
            ArticlePage.objects.live()
            .public()
            .annotate(
                date=Coalesce("publication_date", "first_published_at"),
            )
            .select_related("listing_image", "author", "topic")
            .order_by("-date")
        )

        article_topics = ArticleTopic.objects.filter(
            article_pages__isnull=False
        ).values("title", "slug").distinct().order_by("title")
        matching_topic = False

        article_types = ArticleType.objects.filter(
            article_types__isnull=False
        ).values("title", "slug").distinct().order_by("title")
        matching_type = False

        topic_query_param = request.GET.get("topic")
        if topic_query_param and topic_query_param in article_topics.values_list(
            "slug", flat=True
        ):
            matching_topic = topic_query_param
            queryset = queryset.filter(topic__slug=topic_query_param)

        type_query_param = request.GET.get("type")
        if type_query_param and type_query_param in article_types.values_list(
            "slug", flat=True
        ):
            matching_type = type_query_param
            queryset = queryset.filter(type__slug=type_query_param)


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
        context["types"] = article_types
        context["matching_type"] = matching_type

        return context
