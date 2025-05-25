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
    return generate_slug(text) # Use the more robust general slugifier

def clean_display_name(name_with_potential_prefix_and_ext):
    name_no_ext = Path(name_with_potential_prefix_and_ext).stem
    cleaned = re.sub(r"^\d+-", "", name_no_ext)
    return cleaned.strip()

# --- Frontmatter Parsing Function ---
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

# --- Markdown Extensions ---
# --- Markdown Extensions ---
class HeadingIdAdder(Treeprocessor): # Renamed and updated
    def run(self, root: etree.Element):
        # Treeprocessors are instantiated per Markdown instance (i.e., per file).
        # So, this set will be fresh for each file processed.
        self.used_slugs_on_page = set() # Keep track of slugs used on the current page

        for element in root.iter():
            # Process h1 through h6
            if element.tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6') and element.text:
                base_slug = slugify_heading(element.text) # slugify_heading already calls generate_slug
                final_slug = base_slug
                counter = 1
                # Ensure the slug is unique on the page
                while final_slug in self.used_slugs_on_page:
                    final_slug = f"{base_slug}-{counter}"
                    counter += 1
                element.set('id', final_slug)
                self.used_slugs_on_page.add(final_slug)

class HeadingIdExtension(Extension): # Renamed
    def extendMarkdown(self, md):
        # Use the new class and a new registration key
        md.treeprocessors.register(HeadingIdAdder(md), 'headingidadder', 15)

class AdmonitionProcessorCorrected(BlockProcessor):
    RE_START = re.compile(r'^\s*:::\s*([a-zA-Z0-9_-]+)(?:\s*(.*))?\s*$')
    RE_END = re.compile(r'^\s*:::\s*$')

    def test(self, parent, block):
        return bool(self.RE_START.match(block.split('\n', 1)[0]))

    def run(self, parent, blocks):
        original_block = blocks.pop(0) # The first block matched by test()
        lines = original_block.split('\n')

        first_line_match = self.RE_START.match(lines[0])
        if not first_line_match: # Should not happen if test() is correct
            blocks.insert(0, original_block)
            return False

        admon_type = first_line_match.group(1).lower()
        custom_title_str = first_line_match.group(2).strip() if first_line_match.group(2) else ""
        
        if admon_type == "details":
            display_title = custom_title_str if custom_title_str else "Details"
        else:
            display_title = custom_title_str if custom_title_str else admon_type.capitalize()

        # These lines are the content of the admonition, without any dedenting
        content_lines_raw = []
        
        block_ended = False
        remaining_lines_after_end_in_current_block = []

        # Consume lines from the *current* (first) block
        for i in range(1, len(lines)): # Start from the line after the ':::' directive
            if self.RE_END.match(lines[i]):
                block_ended = True
                # Store any lines in the *same block* that came after the closing :::
                remaining_lines_after_end_in_current_block = lines[i+1:]
                break
            content_lines_raw.append(lines[i]) # Add line as is
        
        # If the end marker ':::' wasn't in the first block, consume subsequent blocks
        if not block_ended:
            while blocks: # Loop through subsequent blocks provided by the parser
                next_block_chunk_from_parser = blocks.pop(0)
                inner_lines_of_chunk = next_block_chunk_from_parser.split('\n')
                processed_all_inner_lines = True # Flag to see if we consumed the whole chunk
                for j, line_in_chunk in enumerate(inner_lines_of_chunk):
                    if self.RE_END.match(line_in_chunk):
                        block_ended = True
                        # If there are lines after ':::' in this chunk, put them back for later processing
                        if j + 1 < len(inner_lines_of_chunk):
                            blocks.insert(0, '\n'.join(inner_lines_of_chunk[j+1:]))
                        processed_all_inner_lines = False 
                        break # Found end marker, stop processing this chunk
                    content_lines_raw.append(line_in_chunk) # Add line as is
                
                if block_ended and not processed_all_inner_lines:
                    break # Exit while blocks loop, end marker found partway through a chunk
                elif block_ended and processed_all_inner_lines:
                    break # Exit while blocks loop, end marker was the last line of a chunk or whole chunk was content

        if not block_ended: # If loop finishes and block_ended is still false, it's an unterminated admonition
            blocks.insert(0, original_block) # Put back the first block
            # Any additionally consumed blocks are effectively lost here if unterminated.
            # Consider more robust error handling or stricter syntax if this is an issue.
            return False

        # Join the raw content lines exactly as they were, preserving their original indentation (or lack thereof)
        parsed_content_for_md = '\n'.join(content_lines_raw)

        # Create the admonition HTML structure
        if admon_type == "details":
            el = etree.SubElement(parent, 'details')
            el.set('class', f'admonition {admon_type}')
            summary_el = etree.SubElement(el, 'summary')
            summary_el.set('class', 'admonition-title')
            summary_el.text = display_title
            content_wrapper_el = etree.SubElement(el, 'div') # Content div after summary
            # content_wrapper_el.set('class', 'admonition-content') # Optional class
        else: # 'info', 'warning', etc.
            el = etree.SubElement(parent, 'div')
            el.set('class', f'admonition {admon_type}')
            title_el = etree.SubElement(el, 'p')
            title_el.set('class', 'admonition-title')
            title_el.text = display_title
            content_wrapper_el = etree.SubElement(el, 'div') # Content div
            # content_wrapper_el.set('class', 'admonition-content') # Optional class
        
        # Recursively parse the collected content block.
        # Fenced_code and other block processors will now operate on this content.
        if parsed_content_for_md.strip(): # Only parse if there's non-whitespace content
             self.parser.parseBlocks(content_wrapper_el, [parsed_content_for_md])
        
        # If there were lines after the ':::' in the original block, put them back
        if remaining_lines_after_end_in_current_block:
            blocks.insert(0, '\n'.join(remaining_lines_after_end_in_current_block))
            
        return True

class AdmonitionExtensionCorrected(Extension):
    def extendMarkdown(self, md):
        # Priority 105 ensures it runs before FencedBlockPreprocessor (priority 95)
        md.parser.blockprocessors.register(AdmonitionProcessorCorrected(md.parser), 'admonition_corrected', 105)

def convert_md_to_html(md_body_text):
    return markdown.markdown(md_body_text, extensions=[
        HeadingIdExtension(), # Use the new, comprehensive extension
        AdmonitionExtensionCorrected(),
        'fenced_code',
        CodeHiliteExtension(css_class='codehilite', guess_lang=False, use_pygments=True),
        'tables' # Removed 'toc' as our extension now handles h1-h6 ID generation
                 # and generate_heading_links builds the visual TOC.
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
    # MODIFIED: Exclude h1-h6 from this list, as their content is indexed via the 'headings' field.
    tags_to_extract_text_from = ['p', 'li', 'td', 'th', 'caption', 'dt', 'dd']
    
    for element in soup.find_all(True):
        is_inside_skipped_tag = False
        current_check = element
        while current_check:
            if current_check.name in ['pre', 'code', 'script', 'style'] or \
               (current_check.has_attr('class') and 'codehilite' in current_check['class']):
                is_inside_skipped_tag = True; break
            current_check = current_check.parent
        if is_inside_skipped_tag: continue

        if element.name in tags_to_extract_text_from: # Hx tags are now skipped here
            # Avoid double-counting admonition titles if they are <p>
            if 'admonition-title' in element.get('class', []) and element.name == 'p':
                pass 
            else:
                 texts.append(element.get_text(separator=' ', strip=True))
        
        # Admonition content extraction (ensure it only gets p and li from within admonition content div)
        if element.name == 'div' and 'admonition' in element.get('class', []):
            # Try to find the specific content wrapper div we added in AdmonitionProcessorCorrected
            # Assuming AdmonitionProcessorCorrected creates a child div for content inside the main admonition div.
            # If your AdmonitionProcessorCorrected directly places <p>, <li> inside the admonition div
            # (after the title), this logic might need adjustment.
            # The current AdmonitionProcessorCorrected in your script does:
            # content_wrapper_el = etree.SubElement(el, 'div')
            # self.parser.parseBlocks(content_wrapper_el, [parsed_content_for_md])
            # So, there should be a child div.
            
            content_wrapper = None
            # Look for the first direct child div that is NOT a title element
            for child in element.children:
                if child.name == 'div' and not (child.has_attr('class') and 'admonition-title' in child.get('class', [])):
                    # For 'details' admonition, the content div is a direct child of 'details'
                    if element.name == 'details':
                        content_wrapper = child
                        break
                    # For other admonitions, it's a child of the main admonition div
                    elif element.name == 'div':
                         content_wrapper = child
                         break
            if not content_wrapper and element.name == 'div': # Fallback if no specific content div found, use the admon div itself
                 content_wrapper = element

            if content_wrapper:
                for sub_el in content_wrapper.find_all(['p', 'li'], recursive=True): # Search recursively within wrapper
                    # Ensure this sub_el is not inside a code block within the admonition
                    is_sub_el_in_code = False
                    sub_check = sub_el
                    # Traverse up to the content_wrapper to check for intermediate code blocks
                    while sub_check and sub_check != content_wrapper: 
                        if sub_check.name in ['pre', 'code'] or \
                           (sub_check.has_attr('class') and 'codehilite' in sub_check['class']):
                            is_sub_el_in_code = True; break
                        sub_check = sub_check.parent
                    
                    # Also ensure the sub_el itself is not an admonition title if it's a <p>
                    if not is_sub_el_in_code and not ('admonition-title' in sub_el.get('class', [])):
                        texts.append(sub_el.get_text(separator=' ', strip=True))

    seen = set()
    # Filter out empty or whitespace-only strings before checking for seen
    unique_texts = [x for x in texts if x and x.strip()]
    # Deduplicate
    unique_texts = [x for x in unique_texts if not (x in seen or seen.add(x))]
    return " ".join(unique_texts)

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

        page_meta, md_body_only_string = parse_metadata_and_body_from_string(full_md_text_from_file)
        
        body_content_html = convert_md_to_html(md_body_only_string)
        toc_table_link_html = generate_heading_links(body_content_html)

        title = page_meta.get('title', file_item["display_title"])

        today = datetime.datetime.today()
        day_suffix = "th"
        if today.day in [1, 21, 31]: day_suffix = "st"
        elif today.day in [2, 22]: day_suffix = "nd"
        elif today.day in [3, 23]: day_suffix = "rd"
        day_str = str(today.day) + day_suffix
        default_date = f"{day_str} {today.strftime('%B %Y')}"
        date = page_meta.get('date', default_date)

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
            "date": page_meta.get('date', None)
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
        json.dump(search_index_entries, f, ensure_ascii=False, indent=None) # indent=None for smaller file size
    print(f"Generated search index: {search_index_file_path}")

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
    server.watch('layout.html', build)
    server.watch('static/**/*', build) # Watch all files and subdirectories in static
    server.serve(root='dist', default_filename='index.html', port=6224)