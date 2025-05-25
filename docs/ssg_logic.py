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
import json
# Removed datetime import

# --- Utility Functions (Keep these as they are) ---
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

# --- Frontmatter Parsing Function (This is essential) ---
def parse_metadata_and_body_from_string(markdown_content_as_string):
    metadata = {}
    body = markdown_content_as_string 
    pattern = re.compile(r'^\s*\+\+\+\s*\n(.*?)\n\s*\+\+\+\s*\n?(.*)', re.DOTALL | re.MULTILINE)
    match = pattern.match(markdown_content_as_string)
    if match:
        frontmatter_text = match.group(1).strip()
        body = match.group(2)
        if frontmatter_text:
            for line in frontmatter_text.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip().lower()] = value.strip()
    return metadata, body

# --- Markdown Extensions (Keep these as they are) ---
class H2ClassAdder(Treeprocessor):
    def run(self, root: etree.Element):
        for element in root.iter():
            if element.tag in ('h2', 'h3', 'h4', 'h5', 'h6') and element.text:
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
        if admon_type == "details": display_title = custom_title_str if custom_title_str else "Details"
        else: display_title = custom_title_str if custom_title_str else admon_type.capitalize()
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
        if remaining_lines_after_end_in_block: blocks.insert(0, "\n".join(remaining_lines_after_end_in_block))
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
        md.parser.blockprocessors.register(AdmonitionProcessorCorrected(md.parser), 'admonition_corrected', 105)

# --- Core Conversion and Generation Functions (Keep these as they are, mostly) ---
def convert_md_to_html(md_body_text):
    return markdown.markdown(md_body_text, extensions=[
        H2ClassExtension(), AdmonitionExtensionCorrected(), 'fenced_code',
        CodeHiliteExtension(css_class='codehilite', guess_lang=False, use_pygments=True),
        'tables', 'toc'
    ])

def generate_heading_links(html_body_content):
    soup = BeautifulSoup(html_body_content, 'html.parser')
    links = []
    for tag in soup.find_all(['h2', 'h3']):
        title = tag.get_text()
        anchor = tag.get('id')
        if not anchor: continue
        link_style = ' style="padding-left:2rem"' if tag.name == 'h3' else ''
        links.append(f'<a href="#{anchor}"{link_style}>{title}</a>')
    return '\n'.join(links)

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('test.html') # This is YOUR template

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
        if not dst_path.exists(): dst_path.mkdir(parents=True, exist_ok=True)
        for item in static_src_path.iterdir():
            s = static_src_path / item.name
            d = dst_path / item.name
            if s.is_dir(): shutil.copytree(s, d, dirs_exist_ok=True)
            else: shutil.copy2(s, d)
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
                "display_title": cleaned_file_display_title,
                "output_file_slug": file_output_slug
            })
    sorted_cleaned_section_titles = sorted(
        temp_sections_by_cleaned_title.keys(),
        key=lambda title: temp_sections_by_cleaned_title[title]["original_sort_key"]
    )
    sidebar_data_for_template = []
    all_files_to_process = [] 
    for cleaned_folder_title in sorted_cleaned_section_titles:
        section_build_data = temp_sections_by_cleaned_title[cleaned_folder_title]
        section_build_data["files"].sort(key=lambda f: (
            f["original_folder_name_for_sort"], f["original_file_name_for_sort"]
        ))
        current_sidebar_section_files = []
        for file_info in section_build_data["files"]:
            current_sidebar_section_files.append({
                "title": file_info["display_title"], "slug": file_info["output_file_slug"]
            })
            all_files_to_process.append({
                "original_path": file_info["original_path"],
                "output_folder_name": section_build_data["output_folder_name"],
                "output_file_slug": file_info["output_file_slug"],
                "display_title": file_info["display_title"]
            })
        if current_sidebar_section_files:
            sidebar_data_for_template.append({
                "title": cleaned_folder_title,
                "output_folder_name": section_build_data["output_folder_name"],
                "files": current_sidebar_section_files
            })
    return all_files_to_process, sidebar_data_for_template

def extract_searchable_text_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    texts = []
    tags_to_extract_text_from = ['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'td', 'th', 'caption', 'dt', 'dd']
    for element in soup.find_all(True):
        is_inside_skipped_tag = False
        current_check = element
        while current_check:
            if current_check.name in ['pre', 'code', 'script', 'style'] or \
               (current_check.has_attr('class') and 'codehilite' in current_check['class']):
                is_inside_skipped_tag = True; break
            current_check = current_check.parent
        if is_inside_skipped_tag: continue
        if element.name in tags_to_extract_text_from:
            if 'admonition-title' in element.get('class', []) and element.name == 'p': pass 
            else: texts.append(element.get_text(separator=' ', strip=True))
        if element.name == 'div' and 'admonition' in element.get('class', []):
            content_wrapper = None
            for child in element.children:
                if child.name == 'div' and not (child.has_attr('class') and 'admonition-title' in child['class']):
                    content_wrapper = child; break
            if content_wrapper:
                for sub_el in content_wrapper.find_all(['p', 'li']):
                    is_sub_el_in_code = False
                    sub_check = sub_el
                    while sub_check and sub_check != content_wrapper:
                        if sub_check.name in ['pre', 'code'] or \
                           (sub_check.has_attr('class') and 'codehilite' in sub_check['class']):
                            is_sub_el_in_code = True; break
                        sub_check = sub_check.parent
                    if not is_sub_el_in_code: texts.append(sub_el.get_text(separator=' ', strip=True))
    seen = set()
    unique_texts = [x for x in texts if x and x.strip() and not (x in seen or seen.add(x))]
    return " ".join(unique_texts)

# --- MODIFIED process_md_files ---
def process_md_files(all_files_to_process, dist_base_path, sidebar_data_for_template):
    search_index_entries = [] 

    for i, file_item in enumerate(all_files_to_process):
        md_path = file_item["original_path"]
        output_folder_name = file_item["output_folder_name"]
        output_file_slug = file_item["output_file_slug"]

        try:
            full_md_text_from_file = md_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading file {md_path}: {e}. Skipping.")
            continue

        # Parse frontmatter and get body
        page_meta, md_body_only_string = parse_metadata_and_body_from_string(full_md_text_from_file)
        
        body_content_html = convert_md_to_html(md_body_only_string)
        toc_table_link_html = generate_heading_links(body_content_html)

        # Use frontmatter title if available, else fallback to filename-derived title
        title = page_meta.get('title', file_item["display_title"])
        date = page_meta.get('date', '')
        # The 'date' from frontmatter will be in page_meta['date'] if it exists

        page_url = f"/{output_folder_name}/{output_file_slug}/"
        
        section_title_for_breadcrumbs = "Unknown Section"
        for sec_data in sidebar_data_for_template:
            if sec_data["output_folder_name"] == output_folder_name:
                section_title_for_breadcrumbs = sec_data["title"]
                break
        breadcrumbs_str = f"{section_title_for_breadcrumbs} > {title}"

        headings_for_index = []
        content_soup = BeautifulSoup(body_content_html, 'html.parser')
        for h_tag in content_soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            tag_text = h_tag.get_text(strip=True)
            tag_id = h_tag.get('id')
            level_match = re.match(r'h([1-6])', h_tag.name)
            if tag_text and tag_id and level_match:
                headings_for_index.append({
                    "level": int(level_match.group(1)), "text": tag_text, "slug": tag_id
                })
        
        searchable_text = extract_searchable_text_from_html(body_content_html)

        search_index_entries.append({
            "id": page_url, "title": title, "breadcrumbs": breadcrumbs_str,
            "url": page_url, "text_content": searchable_text, "headings": headings_for_index,
            "date": page_meta.get('date', None) # Add frontmatter date to search index
        })

        prev_page_data = None
        next_page_data = None
        if i > 0:
            prev_file_item = all_files_to_process[i-1]
            prev_page_data = {
                "title": prev_file_item["display_title"], 
                "url": f"/{prev_file_item['output_folder_name']}/{prev_file_item['output_file_slug']}/"
            }
        if i < len(all_files_to_process) - 1:
            next_file_item = all_files_to_process[i+1]
            next_page_data = {
                "title": next_file_item["display_title"],
                "url": f"/{next_file_item['output_folder_name']}/{next_file_item['output_file_slug']}/"
            }
            
        # These are the variables passed to your test.html
        rendered = template.render(
            body_content=body_content_html,
            toc_table_link=toc_table_link_html,
            sidebar_data=sidebar_data_for_template,
            title=title,
            date=date,
            prev_page_data=prev_page_data,
            next_page_data=next_page_data
        )

        output_dir = dist_base_path / output_folder_name / output_file_slug
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "index.html"
        output_file.write_text(rendered, encoding="utf-8")
        print(f"Generated: {output_file}")

    search_index_file_path = dist_base_path / "search_index.json"
    with open(search_index_file_path, 'w', encoding='utf-8') as f:
        json.dump(search_index_entries, f, ensure_ascii=False, indent=None)
    print(f"Generated search index: {search_index_file_path}")

# --- Build Process and Server (Keep these as they are) ---
_global_sidebar_data_for_redirect = []
def build():
    global _global_sidebar_data_for_redirect
    print("Starting build...")
    dist_path_obj = Path('dist')
    if dist_path_obj.exists(): shutil.rmtree(dist_path_obj)
    dist_path_obj.mkdir(parents=True, exist_ok=True)
    copy_static_assets(static_src_dir='static', dst_dir=str(dist_path_obj))
    all_files_to_process, sidebar_data = scan_src()
    _global_sidebar_data_for_redirect = sidebar_data 
    process_md_files(all_files_to_process, dist_path_obj, sidebar_data)
    if not (dist_path_obj / 'index.html').exists() and _global_sidebar_data_for_redirect:
        if _global_sidebar_data_for_redirect[0]['files']:
            first_section_slug = _global_sidebar_data_for_redirect[0]['output_folder_name']
            first_file_slug = _global_sidebar_data_for_redirect[0]['files'][0]['slug']
            redirect_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Redirecting...</title><meta http-equiv="refresh" content="0; url=/{first_section_slug}/{first_file_slug}/"><link rel="canonical" href="/{first_section_slug}/{first_file_slug}/"></head><body><p>If you are not redirected automatically, follow this <a href='/{first_section_slug}/{first_file_slug}/'>link</a>.</p></body></html>"""
            (dist_path_obj / 'index.html').write_text(redirect_html, encoding='utf-8')
            print(f"Created root redirect to /{first_section_slug}/{first_file_slug}/")
    print("Build complete. Output in 'dist' directory.")

if __name__ == '__main__':
    build()
    server = Server()
    server.watch('src/**/*.md', build)
    server.watch('test.html', build)
    server.watch('static/**/*', build)
    server.serve(root='dist', default_filename='index.html', port=6124)