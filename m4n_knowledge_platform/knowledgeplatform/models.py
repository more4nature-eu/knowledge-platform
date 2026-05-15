from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.models import Orderable
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from ..news.models import ArticlePage, NewsListingPage
from ..utils.models import ArticleTopic, AuthorSnippet

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
class KnowledgeArticleFormat(ArticleTopic):
    pass

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
        return self.author.name

class KnowledgeArticlePage(ArticlePage, ClusterableModel):

    # TODO copy the base template here and delete this
    template = "pages/article_page.html"

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
        blank=False,
        null=False,
        on_delete=models.deletion.PROTECT,
        related_name="pages",
    )

    promote_panels = ArticlePage.promote_panels + [
        FieldPanel("search_keywords"),
    ]

    content_panels = ArticlePage.content_panels[0:1] + [
        InlinePanel("authorships", label="Authors")
    ] + ArticlePage.content_panels[2:-1] + [
        InlinePanel("attached_resources"),
        FieldPanel("article_format"),
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
        index.SearchField("search_keywords")
    ]

    def full_clean(self, *args, **kwargs):
        # We don't use the singular "author" association, but it's defined as non-null
        # on the superclass, so we default it to something sensible here.
        if not self.author_id:
                self.author = AuthorSnippet.objects.get_or_create(title="more4nature")[0]
        super().full_clean(*args, **kwargs)


class KnowledgeHubListingPage(NewsListingPage):

    # TODO copy the base template here and delete this
    template = "pages/news_listing_page.html"

    subpage_types = ["knowledgeplatform.KnowledgeArticlePage"]
    max_count = None

