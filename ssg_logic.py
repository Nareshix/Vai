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
import datetime


def generate_slug(text_to_slugify):
    text = str(text_to_slugify).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text

def slugify_heading(text):
    return generate_slug(text)

def clean_display_name(name_with_potential_prefix_and_ext):
    name_no_ext = Path(name_with_potential_prefix_and_ext).stem
    cleaned = re.sub(r"^\d+-", "", name_no_ext)
    return cleaned.strip()

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


class HeadingIdAdder(Treeprocessor):
    def run(self, root: etree.Element):
        self.used_slugs_on_page = set()
        for element in root.iter():
            if element.tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                full_heading_text = "".join(element.itertext()).strip()
                if full_heading_text:
                    base_slug = slugify_heading(full_heading_text)
                    final_slug = base_slug
                    counter = 1
                    while final_slug in self.used_slugs_on_page:
                        final_slug = f"{base_slug}-{counter}"
                        counter += 1
                    element.set('id', final_slug)
                    self.used_slugs_on_page.add(final_slug)

class HeadingIdExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(HeadingIdAdder(md), 'headingidadder', 15)

class AdmonitionProcessorCorrected(BlockProcessor):
    RE_START = re.compile(r'^\s*:::\s*([a-zA-Z0-9_-]+)(?:\s*(.*))?\s*$')
    RE_END = re.compile(r'^\s*:::\s*$')

    def test(self, parent, block):
        return bool(self.RE_START.match(block.split('\n', 1)[0]))

    def run(self, parent, blocks):
        original_block = blocks.pop(0)
        lines = original_block.split('\n')
        first_line_match = self.RE_START.match(lines[0])
        if not first_line_match:
            blocks.insert(0, original_block)
            return False

        admon_type = first_line_match.group(1).lower()
        custom_title_str = first_line_match.group(2).strip() if first_line_match.group(2) else ""
        
        display_title = custom_title_str if custom_title_str else ("Details" if admon_type == "details" else admon_type.capitalize())

        content_lines_raw = []
        block_ended = False
        remaining_lines_after_end_in_current_block = []

        for i in range(1, len(lines)):
            if self.RE_END.match(lines[i]):
                block_ended = True
                remaining_lines_after_end_in_current_block = lines[i+1:]
                break
            content_lines_raw.append(lines[i])
        
        if not block_ended:
            while blocks:
                next_block_chunk_from_parser = blocks.pop(0)
                inner_lines_of_chunk = next_block_chunk_from_parser.split('\n')
                processed_all_inner_lines = True
                for j, line_in_chunk in enumerate(inner_lines_of_chunk):
                    if self.RE_END.match(line_in_chunk):
                        block_ended = True
                        if j + 1 < len(inner_lines_of_chunk):
                            blocks.insert(0, '\n'.join(inner_lines_of_chunk[j+1:]))
                        processed_all_inner_lines = False
                        break
                    content_lines_raw.append(line_in_chunk)
                if block_ended: break
        
        if not block_ended:
            blocks.insert(0, original_block)
            return False

        parsed_content_for_md = '\n'.join(content_lines_raw)

        if admon_type == "details":
            el = etree.SubElement(parent, 'details')
            el.set('class', f'admonition {admon_type}')
            summary_el = etree.SubElement(el, 'summary')
            summary_el.set('class', 'admonition-title')
            summary_el.text = display_title
            content_wrapper_el = etree.SubElement(el, 'div')
        else:
            el = etree.SubElement(parent, 'div')
            el.set('class', f'admonition {admon_type}')
            title_el = etree.SubElement(el, 'p')
            title_el.set('class', 'admonition-title')
            title_el.text = display_title
            content_wrapper_el = etree.SubElement(el, 'div')
        
        if parsed_content_for_md.strip():
            self.parser.parseBlocks(content_wrapper_el, [parsed_content_for_md])
        
        if remaining_lines_after_end_in_current_block:
            blocks.insert(0, '\n'.join(remaining_lines_after_end_in_current_block))
        return True

class AdmonitionExtensionCorrected(Extension):
    def extendMarkdown(self, md):
        md.parser.blockprocessors.register(AdmonitionProcessorCorrected(md.parser), 'admonition_corrected', 105)

def convert_md_to_html(md_body_text):
    return markdown.markdown(md_body_text, extensions=[
        HeadingIdExtension(), 
        AdmonitionExtensionCorrected(),
        'fenced_code',
        CodeHiliteExtension(css_class='codehilite', guess_lang=False, use_pygments=True),
        'tables'
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
template = env.get_template('layout.html')

def copy_static_assets(static_src_dir='static', dst_dir='dist'):
    static_src_path = Path(static_src_dir)
    dst_path = Path(dst_dir)
    if not static_src_path.exists() or not static_src_path.is_dir():
        print(f"Warning: Static assets directory '{static_src_path}' not found. Skipping copy.")
        return
    print(f"Copying static assets from '{static_src_path}' to '{dst_path}'...")
    try:
        shutil.copytree(static_src_path, dst_path, dirs_exist_ok=True)
    except TypeError:
        print("Falling back to item-by-item copy for static assets (Python < 3.8 or other issue).")
        if not dst_path.exists(): dst_path.mkdir(parents=True, exist_ok=True)
        for item in static_src_path.iterdir():
            s = static_src_path / item.name
            d = dst_path / item.name
            if s.is_dir(): shutil.copytree(s, d, dirs_exist_ok=True)
            else: shutil.copy2(s, d)
    print("Static assets copied successfully.")

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

def process_md_files(all_files_to_process, dist_base_path, sidebar_data_for_template, root_redirect_target_url_for_template):
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

        page_meta, md_body_only_string = parse_metadata_and_body_from_string(full_md_text_from_file)
        body_content_html = convert_md_to_html(md_body_only_string)
        toc_table_link_html = generate_heading_links(body_content_html)

        page_title_from_meta_or_file = page_meta.get('title', file_item["display_title"])
        base_page_url = f"/{output_folder_name}/{output_file_slug}/"
        
        section_title_for_breadcrumbs = "Unknown Section"
        for sec_data in sidebar_data_for_template:
            if sec_data["output_folder_name"] == output_folder_name:
                section_title_for_breadcrumbs = sec_data["title"]
                break
        page_breadcrumbs_base = f"{section_title_for_breadcrumbs} > {page_title_from_meta_or_file}"

        search_index_entries.append({
            "type": "page", "id": base_page_url, "page_title": page_title_from_meta_or_file,
            "display_title": page_title_from_meta_or_file, "breadcrumbs": page_breadcrumbs_base,
            "url": base_page_url, "searchable_text": f"{page_title_from_meta_or_file} {page_breadcrumbs_base}".lower(),
            "date": page_meta.get('date', None)
        })

        content_soup = BeautifulSoup(body_content_html, 'html.parser')
        for h_tag in content_soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = h_tag.get_text(strip=True)
            heading_slug = h_tag.get('id')
            level_match = re.match(r'h([1-6])', h_tag.name)
            if heading_text and heading_slug and level_match:
                heading_level = int(level_match.group(1))
                heading_url = f"{base_page_url}#{heading_slug}"
                heading_display_title = f"{page_title_from_meta_or_file} » {heading_text}"
                heading_breadcrumbs = f"{page_breadcrumbs_base} » {heading_text}"
                search_index_entries.append({
                    "type": "heading", "id": heading_url, "page_title": page_title_from_meta_or_file,
                    "heading_text": heading_text, "heading_level": heading_level,
                    "display_title": heading_display_title, "breadcrumbs": heading_breadcrumbs,
                    "url": heading_url, "searchable_text": f"{page_title_from_meta_or_file} {heading_breadcrumbs} {heading_text}".lower(),
                    "date": page_meta.get('date', None)
                })

        today = datetime.datetime.today()
        day_suffix = "th" if today.day not in [1, 2, 3, 21, 22, 23, 31] else ("st" if today.day in [1, 21, 31] else ("nd" if today.day in [2, 22] else "rd"))
        default_date = f"{str(today.day)}{day_suffix} {today.strftime('%B %Y')}"
        render_date = page_meta.get('date', default_date)

        prev_page_data = None
        if i > 0:
            prev_item = all_files_to_process[i-1]
            prev_page_data = {"title": prev_item["display_title"], "url": f"/{prev_item['output_folder_name']}/{prev_item['output_file_slug']}/"}
        next_page_data = None
        if i < len(all_files_to_process) - 1:
            next_item = all_files_to_process[i+1]
            next_page_data = {"title": next_item["display_title"], "url": f"/{next_item['output_folder_name']}/{next_item['output_file_slug']}/"}
            
        rendered = template.render(
            body_content=body_content_html, toc_table_link=toc_table_link_html,
            sidebar_data=sidebar_data_for_template, title=page_title_from_meta_or_file,
            date=render_date, prev_page_data=prev_page_data, next_page_data=next_page_data,
            root_redirect_target_url=root_redirect_target_url_for_template
        )

        output_dir = dist_base_path / output_folder_name / output_file_slug
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "index.html").write_text(rendered, encoding="utf-8")
        print(f"Generated: {output_dir / 'index.html'}")

    search_index_file_path = dist_base_path / "search_index.json"
    with open(search_index_file_path, 'w', encoding='utf-8') as f:
        json.dump(search_index_entries, f, ensure_ascii=False, indent=None)
    print(f"Generated search index: {search_index_file_path}")
    
_global_sidebar_data_for_redirect = []
_global_root_redirect_target_url = "/" 

# --- IMPORTANT: Define your theme colors here ---
# Replace these with the exact colors from your style.css for dark and light themes
DARK_THEME_BG = '#202124' # Example: A common dark grey
DARK_THEME_TEXT = '#e8eaed' # Example: A light grey/off-white
LIGHT_THEME_BG = '#ffffff' # Example: White
LIGHT_THEME_TEXT = '#202124' # Example: Dark grey/black

MINIFIED_THEME_SCRIPT_TEMPLATE = """<script>(function(){{const t=localStorage.getItem('user-preferred-theme')||(window.matchMedia?.('(prefers-color-scheme: light)').matches?'light':'dark');if(t==='dark'){{document.documentElement.style.backgroundColor='{dark_bg}';document.documentElement.style.color='{dark_text}';}}else{{document.documentElement.style.backgroundColor='{light_bg}';document.documentElement.style.color='{light_text}';}}}})();</script>"""

def build():
    global _global_sidebar_data_for_redirect, _global_root_redirect_target_url
    print("Starting build...")
    dist_path_obj = Path('dist')
    if dist_path_obj.exists(): shutil.rmtree(dist_path_obj)
    dist_path_obj.mkdir(parents=True, exist_ok=True)
    
    copy_static_assets(static_src_dir='static', dst_dir=str(dist_path_obj))
    
    all_files_to_process, sidebar_data = scan_src()
    _global_sidebar_data_for_redirect = sidebar_data

    if sidebar_data and sidebar_data[0].get('files') and len(sidebar_data[0]['files']) > 0:
        first_section_slug_for_root = sidebar_data[0]['output_folder_name']
        first_file_slug_for_root = sidebar_data[0]['files'][0]['slug']
        _global_root_redirect_target_url = f"/{first_section_slug_for_root}/{first_file_slug_for_root}/"
    else:
        _global_root_redirect_target_url = "/" 
    
    process_md_files(all_files_to_process, dist_path_obj, sidebar_data, _global_root_redirect_target_url)

    # Fill the theme script template with actual colors
    theme_script_filled = MINIFIED_THEME_SCRIPT_TEMPLATE.format(
        dark_bg=DARK_THEME_BG,
        dark_text=DARK_THEME_TEXT,
        light_bg=LIGHT_THEME_BG,
        light_text=LIGHT_THEME_TEXT
    )

    for section in sidebar_data:
        if section.get('files') and len(section['files']) > 0:
            section_slug = section['output_folder_name']
            first_file_slug = section['files'][0]['slug']
            redirect_target_url = f"/{section_slug}/{first_file_slug}/"
            section_base_dir_for_redirect = dist_path_obj / section_slug
            section_base_dir_for_redirect.mkdir(parents=True, exist_ok=True) 
            section_redirect_index_file = section_base_dir_for_redirect / "index.html"
            
            redirect_html_content = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Redirecting to {section['title']}</title><meta name="robots" content="noindex, follow">{theme_script_filled}<meta http-equiv="refresh" content="0; url={redirect_target_url}"><link rel="canonical" href="{redirect_target_url}"><style>body{{margin:0;padding:20px;font-family:sans-serif;text-align:center;}}</style></head><body><p>Redirecting to the "{section['title']}" section...</p></body></html>"""
            section_redirect_index_file.write_text(redirect_html_content, encoding='utf-8')
            print(f"Created themed section redirect (with noindex): /{section_slug}/ -> {redirect_target_url}")

    if not (dist_path_obj / 'index.html').exists() and _global_sidebar_data_for_redirect:
        if _global_root_redirect_target_url != "/":
            redirect_html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Redirecting...</title><meta name="robots" content="noindex, follow">{theme_script_filled}<meta http-equiv="refresh" content="0; url={_global_root_redirect_target_url}"><link rel="canonical" href="{_global_root_redirect_target_url}"><style>body{{margin:0;padding:20px;font-family:sans-serif;text-align:center;}}</style></head><body><p>Redirecting...</p></body></html>"""
            (dist_path_obj / 'index.html').write_text(redirect_html, encoding='utf-8')
            print(f"Created themed root redirect (with noindex) to {_global_root_redirect_target_url}")
        else:
            print("Could not create root redirect: No valid target (first section/file) found.")

    print("Build complete. Output in 'dist' directory.")

if __name__ == '__main__':
    build()
    server = Server()
    server.watch('src/**/*.md', build)
    server.watch('layout.html', build)
    server.watch('static/**/*', build) 
    server.serve(root='dist', default_filename='index.html', port=6454)