import re
from pprint import pprint

# --- Core Frontmatter Parsing Function ---
def parse_frontmatter_minimal(markdown_content_as_string):
    """
    Minimal parser for '++++' delimited frontmatter.
    Extracts key:value pairs.
    """
    metadata = {}
    body = markdown_content_as_string # Assume all is body initially

    # Regex to find frontmatter block and separate body
    # ^\s*\+\+\+\+\s*\n   : Start delimiter on its own line
    # (.*?)               : Frontmatter content (non-greedy)
    # \n\s*\+\+\+\+\s*\n? : End delimiter on its own line, optional newline after
    # (.*)                : The rest is the body
    pattern = re.compile(r'^\s*\+\+\+\+\s*\n(.*?)\n\s*\+\+\+\+\s*\n?(.*)', re.DOTALL | re.MULTILINE)
    
    match = pattern.match(markdown_content_as_string)

    if match:
        frontmatter_text = match.group(1).strip() # The lines between ++++
        body = match.group(2)                     # Everything after the second ++++

        if frontmatter_text: # If there's something between the ++++
            for line in frontmatter_text.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1) # Split on first colon only
                    metadata[key.strip().lower()] = value.strip()
        
    return metadata, body

# --- Minimal Test ---
if __name__ == "__main__":
    sample_markdown = """
++++
title: Minimal Test Title
author: Bard
version: 1.0

++++

This is the main body of the document.
It's very simple.
"""

    # Parse it
parsed_meta, parsed_body = parse_frontmatter_minimal(sample_markdown)

pprint(parsed_body)