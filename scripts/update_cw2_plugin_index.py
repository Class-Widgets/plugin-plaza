#!/usr/bin/env python3
import functools
import json
import os
from pathlib import Path

import requests
from cw2_models import CW2ManifestRegistry, CW2PluginJson
from pydantic import ValidationError

print = functools.partial(print, flush=True)

# Class Widgets 2 相关的路径配置
CW2_MANIFEST_DIR = Path("ClassWidgets2/plugins/manifest")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def fetch_cw2_plugin_info(url: str, branch: str, plugin_id: str) -> dict | None:
    """从GitHub仓库获取Class Widgets 2插件的cwplugin.json文件内容"""
    plugin_json_url = f"{url.rstrip('/')}/raw/{branch}/cwplugin.json"
    print(f"🔍 正在拉取: {plugin_id} -> {plugin_json_url}")

    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        response = requests.get(plugin_json_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 拉取失败: {plugin_json_url}, 状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❗ 请求异常: {e}")
    except json.JSONDecodeError:
        print(f"🧨 JSON 解析失败: {plugin_json_url}")
        print(f"返回内容是: {response.text[:200]}...")  # 只打印前200字，防止太长
    return None


def load_existing_cw2_registry() -> dict:
    """加载现有的Class Widgets 2插件清单"""
    registry = {}

    # 如果manifest目录不存在，创建它
    CW2_MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    # 读取所有现有的插件清单文件
    for manifest_file in CW2_MANIFEST_DIR.glob("*.json"):
        if manifest_file.name == "example.plugin.id.json":
            continue  # 跳过示例文件

        try:
            with open(manifest_file, encoding="utf-8") as f:
                plugin_data = json.load(f)
                plugin_id = manifest_file.stem  # 文件名（不含扩展名）作为插件ID
                registry[plugin_id] = plugin_data
                print(f"📁 加载现有插件: {plugin_id}")
        except Exception as e:
            print(f"⚠️ 读取插件清单文件失败 {manifest_file}: {e}")

    return registry


def save_cw2_plugin_manifest(plugin_id: str, plugin_data: dict) -> None:
    """保存插件清单到单独的JSON文件"""
    manifest_path = CW2_MANIFEST_DIR / f"{plugin_id}.json"

    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(plugin_data, f, ensure_ascii=False, indent=4)
        print(f"✅ 保存插件清单: {manifest_path}")
    except Exception as e:
        print(f"❌ 保存插件清单失败 {manifest_path}: {e}")


def update_cw2_plugin_list():
    """更新Class Widgets 2插件清单"""
    print("🚀 开始更新 Class Widgets 2 插件清单...")

    # 加载现有注册表
    existing_registry = load_existing_cw2_registry()

    if not existing_registry:
        print("ℹ️ 未找到现有插件, 任务完成")
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            try:
                with open(github_output, "a", encoding="utf-8") as f:
                    f.write("updated_count=0\n")
            except Exception:
                pass
        return

    # 更新每个插件的信息
    updated_count = 0
    for plugin_id, plugin_info in existing_registry.items():
        if not isinstance(plugin_info, dict):
            print(f"⚠️ 插件 {plugin_id} 的数据格式不正确, 跳过")
            continue

        plugin_data = fetch_cw2_plugin_info(plugin_info["url"], plugin_info["branch"], plugin_id)

        if plugin_data:
            try:
                # 验证并更新插件数据
                pj = CW2PluginJson(**plugin_data)

                # 保持原有的额外字段（如tags）
                updated_plugin_info = plugin_info.copy()
                updated_plugin_info.update(
                    {
                        "name": pj.name or plugin_info.get("name", "未知"),
                        "version": pj.version or plugin_info.get("version", "未知"),
                        "api_version": pj.api_version or plugin_info.get("api_version", "1.0.0"),
                        "description": pj.description or plugin_info.get("description", "未知"),
                        "author": pj.author or plugin_info.get("author", "未知"),
                        "url": pj.url,
                        "branch": pj.branch,
                        "readme": pj.readme,
                        "icon": pj.icon,
                        "tags": pj.tags or plugin_info.get("tags", []),
                    }
                )

                # 保存更新的插件清单
                save_cw2_plugin_manifest(plugin_id, updated_plugin_info)
                updated_count += 1

            except ValidationError as e:
                print(f"⚠️ 插件 {plugin_id} 的 plugin.json 校验失败: {e}")
            except Exception as e:
                print(f"⚠️ 处理插件 {plugin_id} 时出现错误: {e}")
        else:
            print(f"⚠️ 插件 {plugin_id} 更新失败，跳过")

    print(f"✅ Class Widgets 2 插件清单更新完成! 共更新 {updated_count} 个插件")

    # 验证更新后的注册表结构
    try:
        # 重新加载并验证
        updated_registry = load_existing_cw2_registry()
        CW2ManifestRegistry.model_validate(updated_registry)
        print("✅ Class Widgets 2 插件清单结构验证通过")
    except ValidationError as e:
        print("⚠️ Class Widgets 2 插件清单结构验证失败:")
        print(e)

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        try:
            with open(github_output, "a", encoding="utf-8") as f:
                f.write(f"updated_count={updated_count}\n")
        except Exception:
            pass


if __name__ == "__main__":
    update_cw2_plugin_list()
