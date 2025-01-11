import json
import requests

PLUGIN_LIST_PATH = 'Plugins/plugin_list.json'

def fetch_plugin_info(url, branch):
    plugin_json_url = f'{url}/raw/{branch}/plugin.json'
    response = requests.get(plugin_json_url)
    if response.status_code == 200:
        return response.json()
    return None

def update_plugin_list():
    with open(PLUGIN_LIST_PATH, 'r', encoding='utf-8') as f:
        plugin_list = json.load(f)

    for plugin_key, plugin_info in plugin_list.items():
        plugin_data = fetch_plugin_info(plugin_info['url'], plugin_info['branch'])
        if plugin_data:
            plugin_info['version'] = plugin_data['version']
            plugin_info['update_date'] = plugin_data['update_date']

    with open(PLUGIN_LIST_PATH, 'w', encoding='utf-8') as f:
        json.dump(plugin_list, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    update_plugin_list()
