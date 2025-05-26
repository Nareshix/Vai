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
import json
import datetime
import yaml
import argparse
from pathlib import Path
import shutil

def setup_header_in_layout_html():
    DOCS_DIR = Path("docs")  # Define the base path for docs content

    with open(DOCS_DIR / "header_config.yaml", "r") as f:  
        config = yaml.safe_load(f)
    github_link  = config['github_link']
    github_contribution_link = config['github_contribution_link']

    dropdowns = config['dropdowns']
    internals = config['internals']
    externals = config['externals']

    static_dir_in_docs = DOCS_DIR / 'static'
    wanted_basenames = {'favicon', 'logo'}

    found = {}
    if static_dir_in_docs.exists(): 
        for file_path in static_dir_in_docs.rglob('*'):
            if file_path.is_file():
                stem = file_path.stem
                if stem in wanted_basenames:
                    found[stem] = file_path.name
    else:
        print(f"Warning: Static directory '{static_dir_in_docs}' not found. Logo/Favicon might be missing from header.")


    logo = found.get('logo', '')
    favicon = found.get('favicon', '')

    templates_dir_in_docs = DOCS_DIR / 'templates'  
    env = Environment(loader=FileSystemLoader(str(templates_dir_in_docs)))  
    try:
        template = env.get_template('layout_no_header.html')
    except Exception as e:
        print(f"Error: Could not load 'layout_no_header.html' from '{templates_dir_in_docs}'. Details: {e}")
        raise


    rendered = template.render(
        dropdowns=dropdowns,
        internals=internals,
        externals=externals,
        logo=logo,
        favicon=favicon,
        github_link=github_link,
        github_contribution_link=github_contribution_link,
    )

    with open(templates_dir_in_docs / 'layout.html', 'w') as f:  
        f.write(rendered)

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


def copy_static_assets(static_src_dir='static', dst_dir='dist'):
    static_src_path = Path(static_src_dir)
    dst_path = Path(dst_dir)
    if not static_src_path.exists() or not static_src_path.is_dir():
        print(f"Warning: Static assets directory '{static_src_path}' not found. Skipping copy.")
        return
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

    # Sort sections based on original folder names (e.g., "01-Introduction", "02-Setup")
    sorted_cleaned_section_titles = sorted(
        temp_sections_by_cleaned_title.keys(),
        key=lambda title: temp_sections_by_cleaned_title[title]["original_sort_key"]
    )

    sidebar_data_for_template = []
    all_files_to_process = []

    for cleaned_folder_title in sorted_cleaned_section_titles:
        section_build_data = temp_sections_by_cleaned_title[cleaned_folder_title]
        # Sort files within each section based on original file names
        section_build_data["files"].sort(key=lambda f: f["original_file_name_for_sort"])
        
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

def process_md_files(all_files_to_process, dist_base_path, sidebar_data_for_template, jinja_env):
    search_index_entries = []
    page_template = jinja_env.get_template('layout.html')

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
                    "date": page_meta.get('date', None) # Keep date from metadata if present
                })

        today = datetime.datetime.today()
        day_val = today.day
        if 4 <= day_val <= 20 or 24 <= day_val <= 30:
            day_suffix = "th"
        else:
            day_suffix = ["st", "nd", "rd"][day_val % 10 - 1]
        default_date = f"{str(day_val)}{day_suffix} {today.strftime('%B %Y')}"
        render_date = page_meta.get('date', default_date)

        prev_page_data = None
        if i > 0:
            prev_item = all_files_to_process[i-1]
            prev_page_data = {"title": prev_item["display_title"], "url": f"/{prev_item['output_folder_name']}/{prev_item['output_file_slug']}/"}
        
        next_page_data = None
        if i < len(all_files_to_process) - 1:
            next_item = all_files_to_process[i+1]
            next_page_data = {"title": next_item["display_title"], "url": f"/{next_item['output_folder_name']}/{next_item['output_file_slug']}/"}
        
        rendered = page_template.render(
            body_content=body_content_html,
            toc_table_link=toc_table_link_html,
            sidebar_data=sidebar_data_for_template,
            title=page_title_from_meta_or_file,
            date=render_date,
            prev_page_data=prev_page_data,
            next_page_data=next_page_data,

        )

        output_dir = dist_base_path / output_folder_name / output_file_slug
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "index.html").write_text(rendered, encoding="utf-8")

    search_index_file_path = dist_base_path / "search_index.json"
    with open(search_index_file_path, 'w', encoding='utf-8') as f:
        json.dump(search_index_entries, f, ensure_ascii=False, indent=None)
    
_global_sidebar_data_for_redirect = []
_global_root_redirect_target_url = "/" 


def build():
    DOCS_DIR = Path("docs") # Define the base path for docs content

    setup_header_in_layout_html()

    current_env = Environment(
        loader=FileSystemLoader(str(DOCS_DIR / 'templates')),  
        autoescape=True
    )

    global _global_sidebar_data_for_redirect, _global_root_redirect_target_url

    dist_path_obj = DOCS_DIR / 'dist'
    if dist_path_obj.exists():
        shutil.rmtree(dist_path_obj)
    dist_path_obj.mkdir(parents=True, exist_ok=True)

    copy_static_assets(static_src_dir=str(DOCS_DIR / 'static'), dst_dir=str(dist_path_obj))

    all_files_to_process, sidebar_data = scan_src(src_dir_path=str(DOCS_DIR / 'src'))
    _global_sidebar_data_for_redirect = sidebar_data

    if sidebar_data and sidebar_data[0].get('files') and len(sidebar_data[0]['files']) > 0:
        first_section_slug_for_root = sidebar_data[0]['output_folder_name']
        first_file_slug_for_root = sidebar_data[0]['files'][0]['slug']
        _global_root_redirect_target_url = f"/{first_section_slug_for_root}/{first_file_slug_for_root}/"
    else:
        _global_root_redirect_target_url = "/"

    process_md_files(
        all_files_to_process,
        dist_path_obj,
        sidebar_data,
        current_env
    )

    for section in sidebar_data:
        if section.get('files') and len(section['files']) > 0:
            section_slug = section['output_folder_name']
            first_file_in_section_slug = section['files'][0]['slug']

            # Path to the actual content of the first file in this section
            source_html_for_section_index = dist_path_obj / section_slug / first_file_in_section_slug / "index.html"

            # Path for the section's index.html (e.g., docs/dist/introduction/index.html)
            section_index_output_path = dist_path_obj / section_slug / "index.html"

            if source_html_for_section_index.exists():
                # Ensure the section directory itself exists (e.g., docs/dist/introduction/)
                (dist_path_obj / section_slug).mkdir(parents=True, exist_ok=True)

                # Read the content of the first page's HTML in this section
                content_of_first_page_in_section = source_html_for_section_index.read_text(encoding='utf-8')
                # Write this content to the section's index.html
                section_index_output_path.write_text(content_of_first_page_in_section, encoding='utf-8')
                print(f"INFO: Created section index {section_index_output_path} as a copy of content from: {source_html_for_section_index}")
            else:
                print(f"WARNING: Source HTML for section index copy not found at: {source_html_for_section_index}")
                print(f"INFO: Section index for '{section_slug}' will not be created by copying.")
    # --- END OF MODIFIED SECTION INDEX PAGES ---


    # --- CODE FOR ROOT index.html (COPYING CONTENT) ---
    # This part remains the same as your previous correct version
    if not (dist_path_obj / 'index.html').exists() and _global_sidebar_data_for_redirect:
        if _global_root_redirect_target_url != "/":
            try:
                path_parts = _global_root_redirect_target_url.strip('/').split('/')
                if len(path_parts) >= 2:
                    first_section_slug_for_copy = path_parts[0]
                    first_file_slug_for_copy = path_parts[1]
                    source_html_path = dist_path_obj / first_section_slug_for_copy / first_file_slug_for_copy / "index.html"

                    if source_html_path.exists():
                        content_of_first_page = source_html_path.read_text(encoding='utf-8')
                        (dist_path_obj / 'index.html').write_text(content_of_first_page, encoding='utf-8')
                        print(f"INFO: Created root index.html as a copy of content from: {source_html_path}")
                    else:
                        print(f"WARNING: Source HTML for root index.html copy not found at: {source_html_path}")
                        print("INFO: Root index.html will not be created by copying. Ensure 'src' structure is valid or create a 'src/index.md'.")
                else:
                    print("WARNING: Could not determine path components from _global_root_redirect_target_url to copy for root index.html.")
            except Exception as e:
                print(f"ERROR: Occurred while trying to create root index.html by copying: {e}")
        else:
            print("INFO: Could not create root index.html by copying: No valid target (first section/file) found.")
    # --- END OF ROOT index.html CODE ---
    
def cli_init():
    docs_path = Path("docs")
    dist_path = docs_path / "dist"
    src_path = docs_path / "src"
    contributing_file = src_path / "contributing.md"
    static_src = Path("static")
    templates_src = Path("templates")
    static_dst = docs_path / "static"
    templates_dst = docs_path / "templates"
    header_config = Path("header_config.yaml")
    header_config_dst = docs_path / "header_config.yaml"

    if not docs_path.exists():
        dist_path.mkdir(parents=True)
        src_path.mkdir(parents=True)
        contributing_file.touch()

        # Copy static/ and templates/
        if static_src.exists():
            shutil.copytree(static_src, static_dst)
        else:
            print("Warning: 'static/' folder not found.")

        if templates_src.exists():
            shutil.copytree(templates_src, templates_dst)
        else:
            print("Warning: 'templates/' folder not found.")

        # Copy header_config.yaml
        if header_config.exists():
            shutil.copy(header_config, header_config_dst)
        else:
            print("Warning: 'header_config.yaml' not found.")
        print("Created 'docs' folder")
    else:
        print("'docs' folder already exists.")


def cli_run():
    build() 
    server = Server()
    server.watch('docs/src/**/*.md', build)
    server.watch('docs/templates/layout_no_header.html', build) 
    server.watch('docs/static/**/*', build) 
    server.watch('docs/header_config.yaml', build) 
    
    server.serve(root='docs/dist', default_filename='index.html', port=6455)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="Create 'docs' folder structure.")
    subparsers.add_parser("run", help="Run the tool.")

    args = parser.parse_args()

    if args.command == "init":
        cli_init()
    elif args.command == "run":
        cli_run()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()


