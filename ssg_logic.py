import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from xml.etree import ElementTree as etree # Use etree consistently
import re
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.blockprocessors import BlockProcessor
from livereload import Server

# -----------------------------------------
# Heading links generator (Your existing code - seems fine)
# -----------------------------------------
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

# -----------------------------------------
# Slugify function for heading IDs (Your existing code - seems fine)
# -----------------------------------------
def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text

# -----------------------------------------
# Custom Treeprocessor for heading IDs (Your existing code - seems fine)
# -----------------------------------------
class H2ClassAdder(Treeprocessor):
    def run(self, root: etree.Element): # Changed ET.Element to etree.Element
        for element in root.iter():
            if element.tag in ('h2', 'h3') and element.text:
                element.set('id', slugify(element.text))

class H2ClassExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(H2ClassAdder(md), 'h2classadder', 15)

# -----------------------------------------
# CORRECTED Admonition block processor
# -----------------------------------------
class AdmonitionProcessorCorrected(BlockProcessor):
    RE_START = re.compile(r'^\s*:::\s*([a-zA-Z0-9_-]+)(?:\s*(.*))?\s*$') # Start: ::: type [title]
    RE_END = re.compile(r'^\s*:::\s*$')                                # End: :::

    def test(self, parent, block):
        # Test if the first line of the 'block' string matches the start pattern.
        # 'block' is a string that the BlockParser has identified,
        # potentially containing multiple lines if no blank lines separate them.
        return bool(self.RE_START.match(block.split('\n', 1)[0]))

    def run(self, parent, blocks):
        # 'blocks' is a list of block strings for the whole document.
        # We operate on the first one, which our test() method approved.
        current_block_text = blocks.pop(0) # Consume the matched block
        lines = current_block_text.split('\n')

        first_line_match = self.RE_START.match(lines[0])
        if not first_line_match: # Should not happen if test() worked
            blocks.insert(0, current_block_text) # Put it back
            return False 

        admon_type = first_line_match.group(1).lower()
        # Get custom title, or empty string if not present
        custom_title_str = first_line_match.group(2).strip() if first_line_match.group(2) else ""

        # Determine the display title
        if admon_type == "details":
            display_title = custom_title_str if custom_title_str else "Details"
        else:
            # Use custom title if provided, otherwise uppercase the type (e.g., INFO, TIP)
            display_title = custom_title_str if custom_title_str else admon_type.upper()

        # Collect content lines from *within* the current_block_text
        content_lines = []
        end_marker_found_at_index = -1
        
        # Start searching for content and end marker from the second line (lines[1])
        for i in range(1, len(lines)):
            if self.RE_END.match(lines[i]):
                end_marker_found_at_index = i
                break # Found the end marker
            content_lines.append(lines[i])
        
        if end_marker_found_at_index == -1:
            # No closing ':::' found within this block.
            # Put the original block back and let other processors handle it.
            blocks.insert(0, current_block_text)
            return False

        # If there were lines after the ':::' within the same original block string,
        # they need to be put back for further processing.
        remaining_lines_after_end_in_block = lines[end_marker_found_at_index + 1:]
        if remaining_lines_after_end_in_block:
            # Join them back into a block string and insert at the beginning of 'blocks'
            blocks.insert(0, "\n".join(remaining_lines_after_end_in_block))
        
        # Create the HTML elements using etree
        if admon_type == "details":
            el = etree.SubElement(parent, 'details')
            el.set('class', f'admonition {admon_type}')
            summary_el = etree.SubElement(el, 'summary')
            summary_el.set('class', 'admonition-title')
            summary_el.text = display_title # Titles generally aren't further Markdown processed
        else:
            el = etree.SubElement(parent, 'div')
            el.set('class', f'admonition {admon_type}')
            title_el = etree.SubElement(el, 'p')
            title_el.set('class', 'admonition-title')
            title_el.text = display_title
        
        content_wrapper_el = etree.SubElement(el, 'div')
        content_wrapper_el.set('class', 'admonition-content')

        # Recursively parse the collected content lines as Markdown blocks
        # The content_lines list might contain text that forms multiple paragraphs,
        # code blocks, lists etc., hence parseBlocks is appropriate.
        self.parser.parseBlocks(content_wrapper_el, content_lines)
        
        return True # Indicate success, this block was processed

class AdmonitionExtensionCorrected(Extension):
    def extendMarkdown(self, md):
        # Register the corrected block processor
        # Priority 105 is generally good, making it run before the default paragraph processor.
        md.parser.blockprocessors.register(
            AdmonitionProcessorCorrected(md.parser), 'admonition_corrected', 105
        )

# -----------------------------------------
# Markdown to HTML converter - MODIFIED to use corrected extension
# -----------------------------------------
def convert_md_to_html(md_text):
    return markdown.markdown(md_text, extensions=[
        H2ClassExtension(),
        AdmonitionExtensionCorrected(), # Use the corrected extension
        'fenced_code',
        CodeHiliteExtension(css_class='codehilite', guess_lang=False, use_pygments=True)
    ])

# -----------------------------------------
# Jinja2 Environment (Your existing code - seems fine)
# -----------------------------------------
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('test.html') # Ensure 'test.html' is your template file name

# -----------------------------------------
# Example usage (Your existing code - seems fine)
# -----------------------------------------
def build():
    with open("example.md", "r", encoding="utf-8") as f:
        md_text = f.read()
    body_content = convert_md_to_html(md_text)
    toc_table_link = generate_heading_links(body_content)
    rendered = template.render(body_content=body_content, toc_table_link=toc_table_link)
    with open("output.html", "w", encoding="utf-8") as f:
        f.write(rendered)
    



build()
server = Server()
server.watch('example.md', build)
server.serve(root='.', default_filename='output.html')
