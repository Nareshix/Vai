import minify_html

minified = minify_html.minify("<p>  Hello, world!  </p>", minify_js=True, remove_processing_instructions=True)

print(minified)