sample_md_content_with_plus_frontmatter = """
++++
title: My Awesome Page from Plus Frontmatter
date: 2024-01-15
author: Test User
tags: plus, test, example
custom_field: Some specific value
++++

This is the main content of the Markdown file.

It can have multiple paragraphs.

## And even headings

- And lists
- Like this one
"""

sample_md_content_without_frontmatter = """
# This page has no frontmatter

Just regular content.
"""

sample_md_content_malformed_frontmatter_start = """
+++ This is not the right start
title: Bad Title
++++

Content.
"""

sample_md_content_malformed_frontmatter_end = """
++++
title: Good Title
+++ This is not the right end

Content.
"""

sample_md_content_empty_frontmatter = """
++++
++++

Content after empty frontmatter.
"""

sample_md_content_only_frontmatter = """
++++
title: Only Frontmatter Here
status: draft
++++
"""