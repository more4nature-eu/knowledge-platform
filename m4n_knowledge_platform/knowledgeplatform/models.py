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

    promote_panels = ArticlePage.promote_panels + [
        FieldPanel("search_keywords"),
    ]

    content_panels = ArticlePage.content_panels[0:1] + [
        InlinePanel("authorships", label="Authors")
    ] + ArticlePage.content_panels[2:-1] + [
        FieldPanel("display_table_of_contents"),
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

