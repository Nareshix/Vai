from bs4 import BeautifulSoup

def add_github_prefix_to_static_resources(html, github_repo_name):
    soup = BeautifulSoup(html, 'html.parser')

    tags_attrs = {
        'link': 'href',
        'script': 'src',
        'img': 'src',
        'a': 'href',  # Added anchor tags
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

# Sample test
html = '''
<a class=sidebar-link href=/asd/wtr/>wtr</a>    
'''

print(add_github_prefix_to_static_resources(html, '/vai/'))
