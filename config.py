def parse(config):
    result = {}

    # Internal links as list of dicts
    result['internal'] = [
        {'header': item.get('header', ''), 'link': item.get('link', '')}
        for item in config.get('internal', [])
    ]

    # External links as list of dicts
    result['external'] = [
        {'header': item.get('header', ''), 'link': item.get('link', '')}
        for item in config.get('external', [])
    ]

    # Dropdowns
    dropdowns_data = config.get('dropdowns', {})
    dropdowns_result = {
        'main_title': dropdowns_data.get('main_title', ''),
        'items': []
    }
    for group in dropdowns_data.get('items', []):
        group_dict = {
            'title': group.get('title', ''),
            'type': group.get('type', ''),
            'items': [
                {'title': item.get('title', ''), 'link': item.get('link', '')}
                for item in group.get('items', [])
            ]
        }
        dropdowns_result['items'].append(group_dict)

    result['dropdowns'] = dropdowns_result

    return result


import yaml

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
    print(config)
data = parse(config)

# Now you have all values in `data` dict
print(data['internal'])  
print(data['dropdowns']['items'][0]['items'][0]['link'])  # access first dropdown item's first link


print(data.keys())