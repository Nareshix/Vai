from pathlib import Path
import minify_html

source_dir = Path("docs/dist")

for file in source_dir.rglob("*"):
    if file.suffix in [".html", ".js", ".css"]:
        content = file.read_text(encoding="utf-8")

        minified = minify_html.minify(
            content,
            minify_js=True,
            minify_css=True,
            preserve_chevron_percent_template_syntax=True,
        )

        file.write_text(minified, encoding="utf-8")

        print(f"Minified: {file}")
