import yaml
from jinja2 import Environment, FileSystemLoader


def setup_header_in_layout_html(): 
    with open("header_config.yaml", "r") as f:
        config = yaml.safe_load(f)
    github_link  = config['github_link']
    dropdowns = config['dropdowns']
    internals = config['internals']
    externals = config['externals']
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('layout_no_header.html')
    rendered = template.render(
        dropdowns=dropdowns,
        internals=internals,
        externals=externals,
        github_link=github_link,
    )

    with open('templates/layout.html', 'w') as f:
        f.write(rendered)
