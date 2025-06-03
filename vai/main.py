# vai/main.py
# nuitka-project: --include-package-data=vai
# nuitka-project: --include-package-data=livereload
# nuitka-project: --mode=app
# nuitka-project: --output-dir=build
# nuitka-project: --company-name="nareshix"
# nuitka-project: --product-name="vai Application"
# nuitka-project: --file-version="0.1.0" 
# nuitka-project: --product-version="0.1.0"
# nuitka-project: --include-package=pygments.lexers
from genericpath import exists
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
import minify_html
import rcssmin
import rjsmin
from importlib.resources import files, as_file

PACKAGE_NAME = "vai"
PACKAGE_DATA_DIR_NAME = "package_defaults" 


def setup_header_in_layout_html():
    """populates layout_no_heading.html in templates from the config.yaml file.
    It populates it with  github_link, edit_this_page_on_github_link
    dropdowns, internals  and externals. after populating it will generate a html file
    called layout.html and parsing will be done trhough this html file 
    """

    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: config.yaml not found.")

    github_link  = config.get('github_link', '')
    edit_this_page_on_github_link = config.get('edit_this_page_on_github_link', '')

    dropdowns = config.get('dropdowns', '')
    internals = config.get('internals', '')
    externals = config.get('externals', '')

    static_dir_name = 'static'
    static_dir = Path(static_dir_name) 
    wanted_basenames = {'favicon', 'logo'}

    found = {}
    if static_dir.exists(): 
        for file_path in static_dir.rglob('*'):
            if file_path.is_file():
                stem = file_path.stem
                if stem in wanted_basenames:
                    found[stem] = file_path.name
    else:
        print(f"Warning: Static directory '{static_dir}' not found. Logo/Favicon might be missing from header.")


    logo = found.get('logo', '')
    favicon = found.get('favicon', '')

    templates_dir_in_docs = Path('templates')
    
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
        edit_this_page_on_github_link=edit_this_page_on_github_link,
    )

    with open(templates_dir_in_docs / 'layout.html', 'w') as f:  
        f.write(rendered)



def generate_slug(text_to_slugify):
    """
    Converts text to URL-friendly text

    Example:
        My Awesome Title!" -> "my-awesome-title"
    """
    text = str(text_to_slugify).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text


# 01-Introduction.md" -> "Introduction
def clean_display_name(name_with_potential_prefix_and_ext):
    """
    Removes the file name numbering and extension. This is done to get the folder name
    so that an index.html can be created in it

    Example:
        01-Introduction.md" -> "Introduction

    Why:
        Introduction will now become a folder and inside it will contain a index.html
        to prevent showing the html extnesion in url bar. User will redirect to your/website/Introduction
        rather than your/website/Introduction.html
    """
    name_no_ext = Path(name_with_potential_prefix_and_ext).stem
    cleaned = re.sub(r"^\d+-", "", name_no_ext)
    return cleaned.strip()



def parse_metadata_and_body_from_string(markdown_content_as_string):
    """
    It looks for this specific syntax

    +++
    title: My Awesome Page
    date: 2023-01-01
    +++

    and seperates it from main body in the md file.
    These values are used as placeholder in their website
    The use of this specific syntax is optional

    If this specific syntax is not found, it returns an empty dict.
    if only one of those parameters are found, returns a dict with
    that parameter only.

    Returns:
        metadata: {title, date}
        body: rest of the md file

    """

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
    """ Automatically add id attributes to HTML heading tags (<h1> to <h6>).
        These IDs are used for creating anchor links (#-links).


    Args:
        Treeprocessor:  argument operate on the XML/ElementTree representation of the Markdown document 
                        after it has been parsed but before it's serialized to HTML
    """ 
    
    def run(self, root: etree.Element):
        self.used_slugs_on_page = set()
        for element in root.iter():
            if element.tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                full_heading_text = "".join(element.itertext()).strip()
                if full_heading_text:
                    base_slug = generate_slug(full_heading_text)
                    final_slug = base_slug
                    counter = 1
                    while final_slug in self.used_slugs_on_page:
                        final_slug = f"{base_slug}-{counter}"
                        counter += 1
                    element.set('id', final_slug)
                    self.used_slugs_on_page.add(final_slug)

class HeadingIdExtension(Extension):
    """register the HeadingIdAdder treeprocessor with the Markdown parser.
    """
    def extendMarkdown(self, md):
        md.treeprocessors.register(HeadingIdAdder(md), 'headingidadder', 15)
        
class AdmonitionProcessorCorrected(BlockProcessor):
    """ parse custom github like alert blocks, which are special highlighted boxes for notes, warnings, tips, etc.
    The syntax looks like:

    :::note warning Custom Title
    This is the content of the note.
    It can span multiple lines.
    :::
    """
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

        if first_line_match.group(2):
            custom_title_str = first_line_match.group(2).strip()
        else:
            custom_title_str = ""


        admon_type = first_line_match.group(1).lower()
        if custom_title_str:
            display_title = custom_title_str
        elif admon_type == "details":
            display_title = "details"
        else:
            display_title = admon_type.capitalize()
                        
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
    """register the AdmonitionProcessorCorrected block processor with the Markdown parser.
    """
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
    """
    Creates an HTML string representing a list of links to H2 and H3 headings on the current page.
    This is used to build an on-page Table of Contents (TOC).
    """
    soup = BeautifulSoup(html_body_content, 'html.parser')
    links = []
    for tag in soup.find_all(['h1', 'h2']):
        title = tag.get_text()
        anchor = tag.get('id')
        if not anchor: continue
        link_style = ' style="padding-left:2rem"' if tag.name == 'h2' else ''
        links.append(f'<a href="#{anchor}"{link_style}>{title}</a>')
    return '\n'.join(links)


def copy_static_assets(static_src_dir='static', dst_dir='dist'):
    """
    Copies an entire directory of static assets from the "static" folder to the "dist" folder
    It is expected for the static assets to contain style.css, script.js, favicon and logo.
    Note: the favicon and logo can be of any format as long as they are a valid images.
    """
    
    static_src_path = Path(static_src_dir)
    dst_path = Path(dst_dir)
    if not static_src_path.exists() or not static_src_path.is_dir():
        print(f"Warning: Static assets directory '{static_src_path}' not found. Skipping copy.")
        return
    shutil.copytree(static_src_path, dst_path, dirs_exist_ok=True)

def scan_src(src_dir_path='src'):
    """
    Scans the source content directory (docs/src/) to discover all Markdown files and organise them.
    
    It returns "all_files_to_process" where it contains info about each md file
    it also returns "sidebar_data_for_template" which  contains data needed for  the sidebar of the page

    Return:
        all_files_to_process: {original_path, output_folder_name, output_file_slug, display_title}
        sidebar_data_for_template: {title, output_folder_name, files}
    """
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
    """
    Takes the list of md files from src and processes each one to generate the final HTML page.
    It also builds the search index
    """    
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
    

def build():
    """converts all the md files from src_md to html files in
    src_html while retaining the folder structure. (numbers will be excluded
    but position retains in frontend)
    """
    sidebar_data_for_redirect = []
    root_redirect_target_url = "/" 


    DOCS_DIR = Path("./") 

    setup_header_in_layout_html()

    current_env = Environment(
        loader=FileSystemLoader(str(DOCS_DIR / 'templates')),  
        autoescape=True
    )


    src_html_path_obg = DOCS_DIR / 'src_html'
    if src_html_path_obg.exists():
        shutil.rmtree(src_html_path_obg)
    src_html_path_obg.mkdir(parents=True, exist_ok=True)

    copy_static_assets(static_src_dir=str(DOCS_DIR / 'static'), dst_dir=str(src_html_path_obg / 'static'))

    all_files_to_process, sidebar_data = scan_src(src_dir_path=str(DOCS_DIR / 'src_md'))
    sidebar_data_for_redirect = sidebar_data

    if sidebar_data and sidebar_data[0].get('files') and len(sidebar_data[0]['files']) > 0:
        first_section_slug_for_root = sidebar_data[0]['output_folder_name']
        first_file_slug_for_root = sidebar_data[0]['files'][0]['slug']
        root_redirect_target_url = f"/{first_section_slug_for_root}/{first_file_slug_for_root}/"
    else:
         root_redirect_target_url = "/"

    process_md_files(
        all_files_to_process,
        src_html_path_obg,
        sidebar_data,
        current_env
    )

    for section in sidebar_data:
        if section.get('files') and len(section['files']) > 0:
            section_slug = section['output_folder_name']
            first_file_in_section_slug = section['files'][0]['slug']

            source_html_for_section_index = src_html_path_obg / section_slug / first_file_in_section_slug / "index.html"

            section_index_output_path = src_html_path_obg / section_slug / "index.html"

            if source_html_for_section_index.exists():
                (src_html_path_obg / section_slug).mkdir(parents=True, exist_ok=True)

                content_of_first_page_in_section = source_html_for_section_index.read_text(encoding='utf-8')
                section_index_output_path.write_text(content_of_first_page_in_section, encoding='utf-8')
            else:
                print(f"WARNING: Source HTML for section index copy not found at: {source_html_for_section_index}")
                
    if not (src_html_path_obg / 'index.html').exists() and  sidebar_data_for_redirect:
        if  root_redirect_target_url != "/":
            try:
                path_parts =  root_redirect_target_url.strip('/').split('/')
                if len(path_parts) >= 2:
                    first_section_slug_for_copy = path_parts[0]
                    first_file_slug_for_copy = path_parts[1]
                    source_html_path = src_html_path_obg / first_section_slug_for_copy / first_file_slug_for_copy / "index.html"

                    if source_html_path.exists():
                        content_of_first_page = source_html_path.read_text(encoding='utf-8')
                        (src_html_path_obg / 'index.html').write_text(content_of_first_page, encoding='utf-8')
                    else:
                        print(f"WARNING: Source HTML for root index.html copy not found at: {source_html_path}")
                else:
                    print("WARNING: Could not determine path components from  root_redirect_target_url to copy for root index.html.")
            except Exception as e:
                print(f"ERROR: Occurred while trying to create root index.html by copying: {e}")

def cli_init():
    """populares current dir with necessary metadata in it
       The metadata includes an 
       1. an empty dist folder
       2. src folder with README.md
       3. static folder with the necessary css and js, icon and favicon files (these image files are expected to be changed)
       4. templates folder containing html files for the parsing of necessary data (yaml or md) to html 
       5. a config.yaml that affects the top bar. This will stay consistent for all pages

    Usage:
        python main.py init (will be different in prod) 
    """
    current_path = Path("./")

    (current_path / "src_html").mkdir(exist_ok=True)
    src_user_path = current_path / "src_md"
    src_user_path.mkdir(exist_ok=True)
    (src_user_path / "README.md").touch() 

    welcome_dir = src_user_path / "1-Welcome"
    welcome_dir.mkdir(exist_ok=True)

    welcome_file = welcome_dir / "1-welcome.md"
    welcome_file.write_text('''

# Welcome to Vai! 🥳


- *Congratulations! You've successfully initialized a new Vai project.* 🎉

---


# This is Your Starting Point 🚀

- This page (`1-welcome.md`) is just a placeholder.
- Feel free to edit it or replace it entirely with your own homepage content.
- You will mostly edit content in the `src_md/` directory.
-  We also have provided `static/` and `templates/` directory for more deeper and advanced customisation 😉 

---

# Resources 📚

*   📖 **Documentation:** [vai-docs.pages.dev](https://vai-docs.pages.dev/)
*   🐞 **Report Issues (GitHub):** [github.com/nareshix/vai/issues](https://github.com/nareshix/vai/issues)

---

# And most importantly... 🥁
- **Happy Building!**  💻
                ''')


    static_dst_in_user_docs = current_path / "static"
    templates_dst_in_user_docs = current_path / "templates"
    config_dst_in_user_docs = current_path / "config.yaml"

    # Get a reference to the 'package_defaults' directory within the installed package
    package_defaults_resource_root = files(PACKAGE_NAME).joinpath(PACKAGE_DATA_DIR_NAME)

    # --- Copy 'static' directory from package_defaults ---
    static_src_in_pkg = package_defaults_resource_root.joinpath("static")
    if static_src_in_pkg.is_dir():
        with as_file(static_src_in_pkg) as static_src_concrete_path:
            shutil.copytree(static_src_concrete_path, static_dst_in_user_docs, dirs_exist_ok=True)
    else:
        print(f"Warning: Default 'static/' folder not found within the package.")

    # --- Copy 'templates' directory from package_defaults ---
    templates_src_in_pkg = package_defaults_resource_root.joinpath("templates")
    if templates_src_in_pkg.is_dir():
        with as_file(templates_src_in_pkg) as templates_src_concrete_path:
            shutil.copytree(templates_src_concrete_path, templates_dst_in_user_docs, dirs_exist_ok=True)
    else:
        print(f"Warning: Default 'templates/' folder not found within the package.")

    # --- Copy 'config.yaml' from package_defaults ---
    config_src_in_pkg = package_defaults_resource_root.joinpath("config.yaml")
    if config_src_in_pkg.is_file():
        with as_file(config_src_in_pkg) as config_concrete_path:
            shutil.copy(config_concrete_path, config_dst_in_user_docs)
    
    print("Initialised Successfully.") 




def add_github_prefix_to_static_resources(html, github_repo_name):
    soup = BeautifulSoup(html, 'html.parser')

    tags_attrs = {
        'link': 'href',
        'script': 'src',
        'img': 'src',
        'a': 'href',

    }

    for tag_name, attr in tags_attrs.items():
        for tag in soup.find_all(tag_name):
            if tag.has_attr(attr):
                # For <a> tags, skip if target="_blank"
                if tag.name == 'a' and tag.get('target') == '_blank':
                    continue
                elif tag.name == 'a':
                    val = tag[attr]
                    if val.startswith('/') and not val.startswith(github_repo_name):
                        new_val = f'{github_repo_name.rstrip("/")}{val}'
                        tag[attr] = new_val
                else:                        
                    val = tag[attr]
                    if '/static' in val and not val.startswith(f'{github_repo_name}/static'):
                        new_val = val.replace('/static', f'{github_repo_name}/static')
                        tag[attr] = new_val

    updated_html = str(soup)
    return updated_html

def cli_build(github=False):
    """
    It first converts all .md files from the src_md folder into .html files in the src_html folder 
    (in case the user runs vai build without running vai run).
    Then, it processes all the .html files in src_html 
    by minimizing the HTML, CSS, and JS, and outputs the final files into the dist folder.
    """

    SRC_HTML_DIR = Path("src_html") 
    DIST_DIR = Path('dist')

    if not Path('src_html').exists():
        print(f"'src_html' folder not created. Please run 'vai init' or ensure it exists.")
        return

    # runs again to convert md to html just in case
    build() 
    
    if not SRC_HTML_DIR.exists() or not any(SRC_HTML_DIR.iterdir()):
        print(f"Error: The directory '{SRC_HTML_DIR}' is empty or does not exist after the build step.")
        print("Please ensure the `build()` function correctly outputs files to this location.")
        return

    if DIST_DIR.exists(): 
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True) 

    print('building...')
    for src_file in SRC_HTML_DIR.rglob("*"): 
        if src_file.is_file():
            relative_path = src_file.relative_to(SRC_HTML_DIR)
            dest_file_path = DIST_DIR / relative_path

            dest_file_path.parent.mkdir(parents=True, exist_ok=True)

            if src_file.suffix == ".html":
                content = src_file.read_text(encoding="utf-8")

                if github:
                    DOCS_DIR = Path("./")
                    with open(DOCS_DIR / "config.yaml", "r") as f:  
                        config = yaml.safe_load(f)
                    github_repo_name = config['github_repo_name']

                    if not github_repo_name.startswith('/'):
                        github_repo_name = '/' + github_repo_name
                    content = add_github_prefix_to_static_resources(content, github_repo_name)
                
                minified = minify_html.minify(
                    content,
                    minify_js=True,
                    minify_css=True,
                    preserve_chevron_percent_template_syntax=True,
                )
                dest_file_path.write_text(minified, encoding="utf-8") 

            elif src_file.suffix == '.js':

                content = src_file.read_text(encoding="utf-8")

                if github:    
                    prefix = github_repo_name
                    pattern1 = r"(fetch\(\s*')[/]search_index\.json(')"
                    replacement = r"\1" + prefix + r"/search_index.json\2"
                    
                    # Testeded with linux diff command and is proven to be accurate
                    content  = re.sub(pattern1, replacement, content)

                    pattern2 = r"(a\.href\s*=\s*)(result\.url\s*;)"
                    replacement2 = r"\1'" + prefix + r"' + \2"
                    content = re.sub(pattern2, replacement2, content)

                minified = rjsmin.jsmin(content)
                dest_file_path.write_text(minified, encoding="utf-8") 

            elif src_file.suffix == '.css':
                content = src_file.read_text(encoding="utf-8")
                minified = rcssmin.cssmin(content)
                dest_file_path.write_text(minified, encoding="utf-8")
            
            else:
                shutil.copy2(src_file, dest_file_path)

    print(f"Build finished! Minified/copied files are in '{DIST_DIR}'.")

def cli_run():
    """starts the dev server"""
    try:
        build() 
        server = Server()
        print('Ctrl+C to stop the server')
        server.watch('src_md/**/*.md', build)
        server.watch('templates/layout_no_header.html', build) 
        server.watch('static/**/*', build) 
        server.watch('config.yaml', build) 
            
        server.serve(root='src_html', default_filename='index.html', port=6600)
    except OSError as e:
        if e.errno ==98:
            print("Error: port 6600 running. please kill it first before rerunning.")
    except Exception as e:
        print(e)
def main():
    """starts the main cli cmds"""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="Create 'docs' folder structure.")
    subparsers.add_parser("run", help="Run the tool.")

    build_parser = subparsers.add_parser("build", help="minify code. After developing, use this and use the generated files in production")
    build_parser.add_argument('--github', action='store_true', help="builds specifically for github")
    
    args = parser.parse_args()
    if args.command == "init":
        cli_init()
    elif args.command == "run":
        cli_run()
    elif args.command == 'build':
        if args.github:
            cli_build(github=True)
        else:
            cli_build()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()