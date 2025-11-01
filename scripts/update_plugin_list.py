import functools
import json
import os

import requests
from models import PluginJson, Registry
from pydantic import ValidationError

print = functools.partial(print, flush=True)

PLUGIN_LIST_PATH = "Plugins/plugin_list.json"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def fetch_plugin_info(url, branch, plugin_key):
    plugin_json_url = f"{url}/raw/{branch}/plugin.json"
    print(f"🔍 正在拉取: {plugin_key} -> {plugin_json_url}")
    try:
        response = requests.get(plugin_json_url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 拉取失败: {plugin_json_url}, 状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❗ 请求异常: {e}")
    except json.JSONDecodeError:
        print(f"🧨 JSON 解析失败: {plugin_json_url}")
        print(f"返回内容是: {response.text[:200]}...")  # 只打印前 200 字, 防止太长
    return None


def update_plugin_list():
    with open(PLUGIN_LIST_PATH, encoding="utf-8") as f:
        raw_registry = json.load(f)
    try:
        validated_registry = Registry.model_validate(raw_registry)
        registry = raw_registry
        print("✅ 插件列表结构验证通过")
    except ValidationError as e:
        print("⚠️ 当前插件列表结构存在问题:")
        print(e)
        registry = raw_registry
    for plugin_key, plugin_info in registry.items():
        if not isinstance(plugin_info, dict):
            print(f"⚠️ 插件 {plugin_key} 的数据格式不正确, 跳过")
            continue
        plugin_data = fetch_plugin_info(plugin_info["url"], plugin_info["branch"], plugin_key)
        if plugin_data:
            try:
                pj = PluginJson.model_validate(plugin_data)
            except ValidationError as e:
                print(f"⚠️ 插件 {plugin_key} 的 plugin.json 校验失败: {e}")
                pj = None
            if pj:
                plugin_info["name"] = pj.name or plugin_info.get("name", "未知")
                plugin_info["description"] = pj.description or plugin_info.get("description", "未知")
                plugin_info["version"] = pj.version or plugin_info.get("version", "未知")
                plugin_info["plugin_ver"] = pj.plugin_ver or plugin_info.get("plugin_ver", 1)
                plugin_info["author"] = pj.author or plugin_info.get("author", "未知")
                plugin_info["update_date"] = pj.update_date
                plugin_info["url"] = pj.url
                plugin_info["branch"] = pj.branch
        else:
            print(f"⚠️ 插件 {plugin_key} 更新失败, 跳过。")

    with open(PLUGIN_LIST_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=4)
    print("✅ 插件列表更新完毕!")


if __name__ == "__main__":
    update_plugin_list()
