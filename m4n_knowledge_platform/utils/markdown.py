from markdownify import ATX, MarkdownConverter

SKIPPED_TAGS = {"svg", "source", "button", "noscript"}

class ExportMarkdownConverter(MarkdownConverter):
    class Options(MarkdownConverter.Options):
        heading_style = ATX
        bullets = "-"

    def convert_img(self, el, text, parent_tags):
        if not el.get("src"):
            return ""
        return super().convert_img(el, text, parent_tags)


def html_to_markdown(root_tag):
    """Convert a BeautifulSoup Tag's contents to a Markdown string."""
    if root_tag is None:
        return ""

    for tag in root_tag.find_all(SKIPPED_TAGS):
        tag.decompose()

    markdown = ExportMarkdownConverter().convert_soup(root_tag)
    return markdown.strip()
