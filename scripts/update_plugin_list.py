import json
import requests
import functools

print = functools.partial(print, flush=True)

PLUGIN_LIST_PATH = 'Plugins/plugin_list.json'

def fetch_plugin_info(url, branch, plugin_key):
    plugin_json_url = f'{url}/raw/{branch}/plugin.json'
    print(f"🔍 正在拉取：{plugin_key} -> {plugin_json_url}")
    try:
        response = requests.get(plugin_json_url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 拉取失败：{plugin_json_url}，状态码：{response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❗ 请求异常：{e}")
    except json.JSONDecodeError as e:
        print(f"🧨 JSON 解析失败：{plugin_json_url}")
        print(f"返回内容是：{response.text[:200]}...")  # 只打印前 200 字，防止太长
    return None

def update_plugin_list():
    with open(PLUGIN_LIST_PATH, 'r', encoding='utf-8') as f:
        plugin_list = json.load(f)

    for plugin_key, plugin_info in plugin_list.items():
        plugin_data = fetch_plugin_info(plugin_info['url'], plugin_info['branch'], plugin_key)
        if plugin_data:
            plugin_info['version'] = plugin_data.get('version', '未知')
            plugin_info['update_date'] = plugin_data.get('update_date', '未知')
        else:
            print(f"⚠️ 插件 {plugin_key} 更新失败，跳过。")

    with open(PLUGIN_LIST_PATH, 'w', encoding='utf-8') as f:
        json.dump(plugin_list, f, ensure_ascii=False, indent=4)
    print("✅ 插件列表更新完毕！")

if __name__ == '__main__':
    update_plugin_list()
