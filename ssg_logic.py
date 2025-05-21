import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
import xml.etree.ElementTree as ET
import re
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup
from markdown.extensions.codehilite import CodeHiliteExtension


def generate_heading_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    
    for tag in soup.find_all(['h2', 'h3']):
        title = tag.get_text()
        anchor = tag.get('id')
        if not anchor:
            continue
        if tag.name == 'h3':
            link = f'<a href="#{anchor}" style="padding-left:2rem">{title}</a>'
        else:
            link = f'<a href="#{anchor}">{title}</a>'
        links.append(link)
    
    return '\n'.join(links)



def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)  # remove non-word chars
    text = re.sub(r'\s+', '-', text)      # replace spaces with dashes
    return text

class H2ClassAdder(Treeprocessor):
    def run(self, root: ET.Element):
        for element in root.iter():
            if element.tag in ('h2', 'h3') and element.text:
                element.set('id', slugify(element.text))
                # if element.tag == 'h3':
                    # element.set('style', 'padding: 1rem;')

class H2ClassExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(H2ClassAdder(md), 'h2classadder', 15)

def convert_md_to_html(md_text):
    return markdown.markdown(md_text, extensions=[H2ClassExtension(), 
                                                  'fenced_code', 
                                                   CodeHiliteExtension(css_class='codehilite', guess_lang=False, use_pygments=True)
])

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('index.html')


# Example usage
md_text = """
# My Awesome Document Title

This is an introductory paragraph. It contains some **bold** text and some *italic* text, as well as a [link to nowhere](#).

## First H2 Section: Simple and Clean

Content under the first H2. We expect this to appear in the TOC and have an ID like `first-h2-section-simple-and-clean`.

We can have lists:
- Item 1
- Item 2
    - Sub-item 2.1 (should not be in TOC)
    - Sub-item 2.2 (should not be in TOC)

And even a horizontal rule:


### First H3: Under the First H2

This is an H3. It should be in the TOC, indented, and have an ID like `first-h3-under-the-first-h2`.
It contains `inline code`.

### Second H3: Also Under First H2

Another H3, to test multiple H3s under a single H2.
ID should be `second-h3-also-under-first-h2`.

## Second H2 Section: Testing Slugification CASES and Punctuation!

This section tests how various characters are handled in slugification.
ID should be `second-h2-section-testing-slugification-cases-and-punctuation`.

It might contain a blockquote:
> This is a blockquote. It shouldn't affect headings.

And a code block:

```python
def test_function():
    # This code should not be processed for headings
    print("Hello from code block")
```
"""

body_content = convert_md_to_html(md_text)
print(body_content)
toc_table_link = generate_heading_links(body_content)

rendered = template.render(body_content=body_content,toc_table_link=toc_table_link )
with open('output.html', 'w', encoding='utf-8') as f:
    f.write(rendered)


