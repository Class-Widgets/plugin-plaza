import json
import requests

PLUGIN_LIST_PATH = 'Plugins/plugin_list.json'

def fetch_plugin_info(url, branch):
    plugin_json_url = f'{url}/raw/{branch}/plugin.json'
    try:
        response = requests.get(plugin_json_url, timeout=10)
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                print(f"⚠️ JSON解析失败: {plugin_json_url}")
                print(f"内容是：{response.text[:200]}...")
        else:
            print(f"❌ 请求失败 {response.status_code}: {plugin_json_url}")
    except requests.RequestException as e:
        print(f"🚨 请求异常: {e} -> {plugin_json_url}")
    return None

def update_plugin_list():
    with open(PLUGIN_LIST_PATH, 'r', encoding='utf-8') as f:
        plugin_list = json.load(f)

    for plugin_key, plugin_info in plugin_list.items():
        print(f"🔄 正在更新插件：{plugin_key}")
        plugin_data = fetch_plugin_info(plugin_info['url'], plugin_info['branch'])
        if plugin_data:
            plugin_info['version'] = plugin_data.get('version', '未知')
            plugin_info['update_date'] = plugin_data.get('update_date', '未知')
        else:
            print(f"⚠️ 插件 {plugin_key} 的 plugin.json 无法获取，跳过更新。")

    with open(PLUGIN_LIST_PATH, 'w', encoding='utf-8') as f:
        json.dump(plugin_list, f, ensure_ascii=False, indent=4)
    print("✅ 插件列表已更新完成！")

if __name__ == '__main__':
    update_plugin_list()
