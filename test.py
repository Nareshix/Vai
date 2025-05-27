from bs4 import BeautifulSoup

# Tags to check and attributes to modify

def add_github_prefix_to_static_resources(html, github_repo_name):
    soup = BeautifulSoup(html, 'html.parser')

    tags_attrs = {
        'link': 'href',
        'script': 'src',
        'img': 'src',
    }

    for tag_name, attr in tags_attrs.items():
        for tag in soup.find_all(tag_name):
            if tag.has_attr(attr):
                val = tag[attr]
                if '/static' in val and not val.startswith(f'/{github_repo_name}/static'):
                    new_val = val.replace('/static', f'{github_repo_name}/static')
                    tag[attr] = new_val

    updated_html = str(soup)
    return updated_html


html = '''
asdf
fd
asdf
as
df
<link rel="icon" href="/staticfavicon.png" />
<link rel="stylesheet" href="/static/style.css"></head>
<script src="/static/script.js" defer></script>
<img src="/static/logo.png" alt="logo" width="38">
<img src="/static/logo.png" alt="logo" width="64">
'''
print((add_github_prefix_to_static_resources(html, '/vai')))