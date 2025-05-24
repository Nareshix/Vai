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
import shutil

def slugify_heading(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text

def generate_slug(text_to_slugify):
    text = str(text_to_slugify).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text

def clean_display_name(name_with_potential_prefix_and_ext):
    name_no_ext = Path(name_with_potential_prefix_and_ext).stem
    cleaned = re.sub(r"^\d+-", "", name_no_ext)
    return cleaned.strip()

class H2ClassAdder(Treeprocessor):
    def run(self, root: etree.Element):
        for element in root.iter():
            if element.tag in ('h2', 'h3') and element.text:
                element.set('id', slugify_heading(element.text))

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
                break
            content_lines.append(lines[i])
        if end_marker_found_at_index == -1:
            blocks.insert(0, current_block_text)
            return False
        remaining_lines_after_end_in_block = lines[end_marker_found_at_index + 1:]
        if remaining_lines_after_end_in_block:
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

def generate_heading_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for tag in soup.find_all(['h2', 'h3']):
        title = tag.get_text()
        anchor = tag.get('id')
        if not anchor:
            continue
        link_style = ' style="padding-left:2rem"' if tag.name == 'h3' else ''
        links.append(f'<a href="#{anchor}"{link_style}>{title}</a>')
    return '\n'.join(links)

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('test.html')

def copy_static_assets(static_src_dir='static', dst_dir='dist'):
    static_src_path = Path(static_src_dir)
    dst_path = Path(dst_dir)

    if not static_src_path.exists() or not static_src_path.is_dir():
        print(f"Warning: Static assets directory '{static_src_path}' not found. Skipping copy.")
        return

    print(f"Copying static assets from '{static_src_path}' to '{dst_path}'...")
    try:
        shutil.copytree(static_src_path, dst_path, dirs_exist_ok=True)
        print("Static assets copied successfully.")
    except TypeError:
        print("Falling back to item-by-item copy for static assets (Python < 3.8 or other issue).")
        for item in static_src_path.rglob('*'): # rglob gets all files and dirs recursively
            relative_path = item.relative_to(static_src_path)
            destination_item = dst_path / relative_path
            if item.is_dir():
                destination_item.mkdir(parents=True, exist_ok=True)
            else:
                # Ensure parent directory of the file exists in the destination
                destination_item.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, destination_item) # copy2 preserves metadata
        print("Static assets copied item by item successfully.")


def scan_src(src_dir_path='src'):
    src_path = Path(src_dir_path)
    temp_sections_by_cleaned_title = {}
    original_top_level_dir_paths = sorted([p for p in src_path.iterdir() if p.is_dir()])

    for dir_path in original_top_level_dir_paths:
        original_folder_name = dir_path.name
        cleaned_section_display_title = clean_display_name(original_folder_name)
        section_output_folder_slug = generate_slug(cleaned_section_display_title)

        if cleaned_section_display_title not in temp_sections_by_cleaned_title:
            temp_sections_by_cleaned_title[cleaned_section_display_title] = {
                "original_sort_key": original_folder_name,
                "output_folder_name": section_output_folder_slug,
                "files": []
            }
        
        md_files_in_dir = sorted(dir_path.glob("*.md"))
        for md_file_path in md_files_in_dir:
            original_file_name_with_ext = md_file_path.name
            cleaned_file_display_title = clean_display_name(original_file_name_with_ext)
            file_output_slug = generate_slug(cleaned_file_display_title)
            
            temp_sections_by_cleaned_title[cleaned_section_display_title]["files"].append({
                "original_path": md_file_path,
                "original_folder_name_for_sort": original_folder_name,
                "original_file_name_for_sort": original_file_name_with_ext,
                "display_title": cleaned_file_display_title, # Store for easy access
                "output_file_slug": file_output_slug
            })

    sorted_cleaned_section_titles = sorted(
        temp_sections_by_cleaned_title.keys(),
        key=lambda title: temp_sections_by_cleaned_title[title]["original_sort_key"]
    )

    sidebar_data_for_template = []
    all_files_to_process = [] # This will store all pages in their global sorted order

    for cleaned_folder_title in sorted_cleaned_section_titles:
        section_build_data = temp_sections_by_cleaned_title[cleaned_folder_title]
        section_build_data["files"].sort(key=lambda f: (
            f["original_folder_name_for_sort"],
            f["original_file_name_for_sort"]
        ))
        
        current_sidebar_section_files = []
        for file_info in section_build_data["files"]:
            current_sidebar_section_files.append({
                "title": file_info["display_title"],
                "slug": file_info["output_file_slug"]
            })
            # Add to the global list for processing and prev/next links
            all_files_to_process.append({
                "original_path": file_info["original_path"],
                "output_folder_name": section_build_data["output_folder_name"],
                "output_file_slug": file_info["output_file_slug"],
                "display_title": file_info["display_title"] # Needed for prev/next title
            })
        
        if current_sidebar_section_files:
            sidebar_data_for_template.append({
                "title": cleaned_folder_title,
                "output_folder_name": section_build_data["output_folder_name"],
                "files": current_sidebar_section_files
            })
            
    return all_files_to_process, sidebar_data_for_template

def process_md_files(all_files_to_process, dist_base_path, sidebar_data_for_template):
    # all_files_to_process is already globally sorted
    for i, file_item in enumerate(all_files_to_process):
        md_path = file_item["original_path"]
        output_folder_name = file_item["output_folder_name"]
        output_file_slug = file_item["output_file_slug"]

        md_text = md_path.read_text(encoding="utf-8")
        body_content = convert_md_to_html(md_text)
        toc_table_link = generate_heading_links(body_content)

        # Determine previous and next page data
        prev_page_data = None
        next_page_data = None

        if i > 0: # If not the first file
            prev_file_item = all_files_to_process[i-1]
            prev_page_data = {
                "title": prev_file_item["display_title"], 
                "url": f"/{prev_file_item['output_folder_name']}/{prev_file_item['output_file_slug']}/"
            }

        if i < len(all_files_to_process) - 1: # If not the last file
            next_file_item = all_files_to_process[i+1]
            next_page_data = {
                "title": next_file_item["display_title"],
                "url": f"/{next_file_item['output_folder_name']}/{next_file_item['output_file_slug']}/"
            }

        rendered = template.render(
            body_content=body_content,
            toc_table_link=toc_table_link,
            sidebar_data=sidebar_data_for_template,
            prev_page_data=prev_page_data, # Add to template context
            next_page_data=next_page_data  # Add to template context
        )

        output_dir = dist_base_path / output_folder_name / output_file_slug
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "index.html"
        output_file.write_text(rendered, encoding="utf-8")
        print(f"Generated: {output_file}")

# Store sidebar_data globally for the root index.html redirect
# This is a bit of a hack; a more robust solution might involve passing it around or re-calculating
_global_sidebar_data_for_redirect = []

def build():
    global _global_sidebar_data_for_redirect
    print("Starting build...")
    dist_path_obj = Path('dist')

    # 1. Clean the dist directory
    if dist_path_obj.exists():
        shutil.rmtree(dist_path_obj)
    dist_path_obj.mkdir(parents=True, exist_ok=True)

    # 2. Copy static assets from 'static/' to 'dist/'
    copy_static_assets(static_src_dir='static', dst_dir=str(dist_path_obj))

    # 3. Scan source and get data for pages and sidebar
    all_files_to_process, sidebar_data = scan_src()
    _global_sidebar_data_for_redirect = sidebar_data # Store for redirect logic
    
    # 4. Process markdown files and generate HTML
    process_md_files(all_files_to_process, dist_path_obj, sidebar_data)

    # 5. Create root index.html redirect (optional, but good for UX)
    if not (dist_path_obj / 'index.html').exists() and _global_sidebar_data_for_redirect:
        if _global_sidebar_data_for_redirect[0]['files']:
            first_section_slug = _global_sidebar_data_for_redirect[0]['output_folder_name']
            first_file_slug = _global_sidebar_data_for_redirect[0]['files'][0]['slug']
            redirect_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Redirecting...</title><meta http-equiv="refresh" content="0; url=/{first_section_slug}/{first_file_slug}/"><link rel="canonical" href="/{first_section_slug}/{first_file_slug}/"></head><body><p>If you are not redirected automatically, follow this <a href='/{first_section_slug}/{first_file_slug}/'>link</a>.</p></body></html>"""
            (dist_path_obj / 'index.html').write_text(redirect_html, encoding='utf-8')
            print(f"Created root redirect to /{first_section_slug}/{first_file_slug}/")

    print("Build complete. Output in 'dist' directory.")

if __name__ == '__main__':
    build() # Initial build
    server = Server()
    server.watch('src/**/*.md', build)
    server.watch('test.html', build)
    server.watch('static/**/*', build) # Watch static assets for changes too
    server.serve(root='dist', default_filename='index.html', port=6120)