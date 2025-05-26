import yaml
from jinja2 import Environment, FileSystemLoader


def setup_header_in_layout_html(): 
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    github_link  = config['github_link']
    dropdowns = config['dropdowns']
    internals = config['internals']
    externals = config['externals']
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('layout_jinja.html')
    rendered = template.render(
        dropdowns=dropdowns,
        internals=internals,
        externals=externals,
        github_link=github_link,
    )

    print(dropdowns)

    with open('layout.html', 'w') as f:
        f.write(rendered)

setup_header_in_layout_html()