from pprint import pprint
import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from xml.etree import ElementTree as etree 
import re
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.blockprocessors import BlockProcessor
from livereload import Server
from pathlib import Path

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

class H2ClassAdder(Treeprocessor):
    def run(self, root: etree.Element): 
        for element in root.iter():
            if element.tag in ('h2', 'h3') and element.text:
                element.set('id', slugify(element.text))

class H2ClassExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(H2ClassAdder(md), 'h2classadder', 15)

class AdmonitionProcessorCorrected(BlockProcessor):
    RE_START = re.compile(r'^\s*:::\s*([a-zA-Z0-9_-]+)(?:\s*(.*))?\s*$') 
    RE_END = re.compile(r'^\s*:::\s*$')                                

    def test(self, parent, block):
        return bool(self.RE_START.match(block.split('\n', 1)[0]))

    def run(self, parent, blocks):
        current_block_text = blocks.pop(0) 
        lines = current_block_text.split('\n')

        first_line_match = self.RE_START.match(lines[0])
        if not first_line_match:
            blocks.insert(0, current_block_text)
            return False 

        admon_type = first_line_match.group(1).lower()
        custom_title_str = first_line_match.group(2).strip() if first_line_match.group(2) else ""

        if admon_type == "details":
            display_title = custom_title_str if custom_title_str else "Details"
        else:
            display_title = custom_title_str if custom_title_str else admon_type.upper()

        content_lines = []
        end_marker_found_at_index = -1
        
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
        
        if admon_type == "details":
            el = etree.SubElement(parent, 'details')
            el.set('class', f'admonition {admon_type}')
            summary_el = etree.SubElement(el, 'summary')
            summary_el.set('class', 'admonition-title')
            summary_el.text = display_title 
        else:
            el = etree.SubElement(parent, 'div')
            el.set('class', f'admonition {admon_type}')
            title_el = etree.SubElement(el, 'p')
            title_el.set('class', 'admonition-title')
            title_el.text = display_title
        
        content_wrapper_el = etree.SubElement(el, 'div')

        self.parser.parseBlocks(content_wrapper_el, content_lines)
        
        return True

class AdmonitionExtensionCorrected(Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(
            AdmonitionProcessorCorrected(md.parser), 'admonition_corrected', 105
        )

def convert_md_to_html(md_text):
    return markdown.markdown(md_text, extensions=[
        H2ClassExtension(),
        AdmonitionExtensionCorrected(),
        'fenced_code',
        CodeHiliteExtension(css_class='codehilite', guess_lang=False, use_pygments=True)
    ])

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('test.html')



# -----------------------------------------
# Function to dynamically generate sidebar_data
# -----------------------------------------

from pathlib import Path


def scan_src(src='src', dst='dist'):
    sidebar_data = []
    src = Path(src)
    dist = Path(dst)
    dist.mkdir(parents=True, exist_ok=True)

    folders = set()
    files = []

    for path in src.rglob("*.md"):
        # Get folder and filename without prefix number
        relative = path.relative_to(src)
        folder = relative.parts[0].split('-', 1)[1]  # e.g. 'Reference'
        file_name = relative.name  # 'getting started.md'
        files.append((folder, path))
        folders.add(folder)

    # Create all main folders under dist
    for folder in folders:
        (dist / folder).mkdir(parents=True, exist_ok=True)

    # Build sidebar_data
    for folder in folders:
        folder_files = [f[1].stem for f in files if f[0] == folder]
        sidebar_data.append({
            "title": folder,
            "files": folder_files
        })

    return files, dist, sidebar_data

def process_md_files(files, dist, sidebar_data):
    for folder, md_path in files:
        md_text = md_path.read_text(encoding="utf-8")
        body_content = convert_md_to_html(md_text)
        toc_table_link = generate_heading_links(body_content)

        rendered = template.render(
            body_content=body_content,
            toc_table_link=toc_table_link,
            sidebar_data=sidebar_data
        )

        # Write to dist/{folder}/{filename_without_ext}/index.html
        output_dir = dist / folder / md_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "index.html"
        output_file.write_text(rendered, encoding="utf-8")

def build():
    files, dist, sidebar_data = scan_src()
    process_md_files(files, dist, sidebar_data)
    

build()
server = Server()
server.watch('src/**/*.md', build)
server.serve(root='dist', default_filename='index.html', port=6120)

