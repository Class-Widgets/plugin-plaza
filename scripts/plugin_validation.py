import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import requests
from models import Registry, RegistryItem, Submission
from pydantic import ValidationError


def fetch_plugin_json_from_repo(repo_url: str, branch: str = "main") -> dict[str, Any] | None:
    """从GitHub仓库获取plugin.json文件内容"""
    try:
        if not repo_url.startswith("https://github.com/"):
            return None
        repo_url = repo_url.rstrip("/")
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]
        raw_url = repo_url.replace("https://github.com/", "https://raw.githubusercontent.com/")
        plugin_json_url = f"{raw_url}/{branch}/plugin.json"
        headers = {}
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        response = requests.get(plugin_json_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None


def extract_form_data_from_issue(issue_body: str) -> dict[str, str] | None:
    """从Issue表单中提取信息"""
    try:
        data = {}

        url_match = re.search(r"### 插件仓库 URL\s*\n\s*(.+)", issue_body)
        if url_match:
            data["url"] = url_match.group(1).strip()
        id_match = re.search(r"### 插件 ID\s*\n\s*(.+)", issue_body)
        if id_match:
            data["id"] = id_match.group(1).strip()
        tag_match = re.search(r"### 插件标签\s*\n\s*(.+)", issue_body)
        if tag_match:
            data["tag"] = tag_match.group(1).strip()
        branch_match = re.search(r"### 插件分支\s*\n\s*(.+)", issue_body)
        if branch_match:
            data["branch"] = branch_match.group(1).strip()
        else:
            data["branch"] = "main"

        return data if all(k in data for k in ["url", "id", "tag", "branch"]) else None
    except Exception:
        return None


def build_comment_formatted(success: bool, errors: list[str], formatted_json: str) -> str:
    """构建评论内容"""
    if success:
        return f"""<!-- plugin-review -->
✅ **验证通过**

**插件元数据:**
```json
{formatted_json}
```

---
**操作选项:**
- [ ] 勾选此选项执行提交

> 编辑此评论勾选相应选项来触发操作"""
    else:
        error_text = "\n".join(f"- {err}" for err in errors)
        return f"""<!-- plugin-review -->
❌ **验证未通过**

**错误信息:**
{error_text}

> 请修复上述错误后重新验证"""


def validate_submission_metadata(data: dict[str, Any]) -> tuple[bool, list[str], RegistryItem | None]:
    """验证提交的元数据"""
    errors = []

    try:
        submission = Submission(**data)
        registry_item = RegistryItem(
            id=submission.id,
            name=submission.name,
            version=submission.version,
            plugin_ver=submission.plugin_ver,
            author=submission.author,
            url=submission.url,
            branch=submission.branch,
            tag=submission.tag,
            description=submission.description,
        )

        return True, [], registry_item

    except ValidationError as e:
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            errors.append(f"{field}: {error['msg']}")
        return False, errors, None
    except Exception as e:
        errors.append(f"验证过程中出现错误: {e!s}")
        return False, errors, None


def validate_submission() -> None:
    """验证提交的插件元数据"""
    issue_body = os.getenv("ISSUE_BODY", "")
    if not issue_body:
        print("❌ 未找到Issue内容")
        return
    form_data = extract_form_data_from_issue(issue_body)
    if not form_data:
        comment = """<!-- plugin-review -->
❌ **验证失败**

无法从Issue表单中提取必要信息,请确保正确填写了以下字段:
- 插件仓库 URL
- 插件 ID
- 插件标签
"""

        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        with open(artifacts_dir / "comment.md", "w", encoding="utf-8") as f:
            f.write(comment)
        return
    plugin_json = fetch_plugin_json_from_repo(form_data["url"], form_data["branch"])
    if not plugin_json:
        comment = f"""<!-- plugin-review -->
❌ **验证失败**

无法从仓库获取 `plugin.json` 文件:
- 仓库URL: `{form_data["url"]}`
- 请确保仓库是公开的且包含有效的 `plugin.json` 文件
"""

        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        with open(artifacts_dir / "comment.md", "w", encoding="utf-8") as f:
            f.write(comment)
        return
    merged_data = {
        "id": form_data["id"],
        "tag": form_data["tag"],
        "url": form_data["url"],
        "branch": plugin_json.get("branch", "main"),
        **plugin_json,  # plugin.json中的数据会覆盖同名字段
    }

    success, errors, registry_item = validate_submission_metadata(merged_data)

    if success and registry_item:
        validation_result = {
            "success": True,
            "registry_item": registry_item.model_dump(),
            "plugin_id": form_data["id"],
            "form_data": form_data,
            "plugin_json": plugin_json,
        }

        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        with open(artifacts_dir / "validation_result.json", "w", encoding="utf-8") as f:
            json.dump(validation_result, f, indent=2, ensure_ascii=False)
        formatted_json = json.dumps(registry_item.model_dump(), indent=2, ensure_ascii=False)
        comment = f"""<!-- plugin-review -->
✅ **验证通过**

**插件信息:**
- **ID**: `{form_data["id"]}`
- **名称**: {registry_item.name}
- **版本**: {registry_item.version}
- **作者**: {registry_item.author}
- **描述**: {registry_item.description or "无"}

**完整元数据:**
```json
{formatted_json}
```

**操作选项:**
- [ ] 执行提交 (勾选此项将插件添加到市场)
"""
    else:
        validation_result = {"success": False, "errors": errors, "form_data": form_data, "plugin_json": plugin_json}
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        with open(artifacts_dir / "validation_result.json", "w", encoding="utf-8") as f:
            json.dump(validation_result, f, indent=2, ensure_ascii=False)
        error_text = "\n".join(f"- {error}" for error in errors)
        comment = f"""<!-- plugin-review -->
❌ **验证失败**

**错误信息:**
{error_text}

**获取到的plugin.json内容:**
```json
{json.dumps(plugin_json, indent=2, ensure_ascii=False)}
```
"""

    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    with open(artifacts_dir / "comment.md", "w", encoding="utf-8") as f:
        f.write(comment)


def handle_toggle() -> None:
    """处理复验/提交勾选"""
    issue_body = os.getenv("ISSUE_BODY", "")
    comment_body = os.getenv("COMMENT_BODY", "")

    if not issue_body:
        print("❌ 缺少必要的环境变量")
        sys.exit(1)
    revalidate_checked = "- [x] 重新验证" in issue_body
    submit_checked = comment_body and "- [x] 勾选此选项执行提交" in comment_body
    resubmit_checked = comment_body and "- [x] 尝试重新提交" in comment_body
    if revalidate_checked:
        print("🔄 触发重新验证")
        updated_body = issue_body.replace("- [x] 重新验证", "- [ ] 重新验证")
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        with open(artifacts_dir / "updated_issue_body.txt", "w", encoding="utf-8") as f:
            f.write(updated_body)

        validate_submission()  # 重新验证
        return

    if submit_checked or resubmit_checked:
        try:
            with open("artifacts/validation_result.json", encoding="utf-8") as f:
                validation_result = json.load(f)
            registry_item_data = validation_result["registry_item"]
            plugin_id = validation_result["plugin_id"]
            if "id" in registry_item_data:
                del registry_item_data["id"]
            plugin_list_path = Path("Plugins/plugin_list.json")
            if plugin_list_path.exists():
                with open(plugin_list_path, encoding="utf-8") as f:
                    plugin_list = json.load(f)
            else:
                plugin_list = {}
            plugin_list[plugin_id] = registry_item_data
            with open(plugin_list_path, "w", encoding="utf-8") as f:
                json.dump(plugin_list, f, indent=4, ensure_ascii=False)
            with open("artifacts/commit.flag", "w") as f:
                f.write("true")
            with open("artifacts/plugin_to_add.json", "w", encoding="utf-8") as f:
                json.dump({plugin_id: registry_item_data}, f, indent=2, ensure_ascii=False)

            comment = f"""<!-- plugin-review -->
🎉 **感谢您的贡献, 插件已成功添加到市场!**

**插件信息:**
- **名称:** {registry_item_data.get("name", plugin_id)}
- **版本:** {registry_item_data.get("version", "未知")}
- **作者:** {registry_item_data.get("author", "未知")}

---
✅ 插件现在可以在插件市场中找到。感谢您的贡献!"""

            artifacts_dir = Path("artifacts")
            artifacts_dir.mkdir(exist_ok=True)
            with open(artifacts_dir / "comment.md", "w", encoding="utf-8") as f:
                f.write(comment)

        except Exception as e:
            comment = f"""<!-- plugin-review -->
❌ **提交失败**

处理提交时出现错误: {e!s}

---
**操作选项:**
- [ ] 尝试重新提交

> 编辑此评论勾选相应选项来触发操作"""
            artifacts_dir = Path("artifacts")
            artifacts_dir.mkdir(exist_ok=True)
            with open(artifacts_dir / "comment.md", "w", encoding="utf-8") as f:
                f.write(comment)


def validate_registry() -> None:
    """验证注册表结构"""
    registry_file = Path("Plugins/plugin_list.json")
    if not registry_file.exists():
        print("❌ 注册表文件不存在")
        sys.exit(1)

    try:
        with open(registry_file, encoding="utf-8") as f:
            data = json.load(f)
        registry = Registry.model_validate(data)
        print(f"✅ 注册表验证通过, 包含 {len(registry.root)} 个插件")
        summary = f"✅ **注册表验证通过**\n\n- 插件总数: {len(registry.root)}\n- 验证时间: {os.getenv('GITHUB_RUN_ID', 'unknown')}"
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        with open(artifacts_dir / "validation_summary.md", "w", encoding="utf-8") as f:
            f.write(summary)

    except ValidationError as e:
        errors = []
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            errors.append(f"{field}: {error['msg']}")
        error_text = "\n".join(f"- {err}" for err in errors)
        print(f"❌ 注册表验证失败: \n{error_text}")
        summary = f"❌ **注册表验证失败**\n\n**错误信息: **\n{error_text}"
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        with open(artifacts_dir / "validation_summary.md", "w", encoding="utf-8") as f:
            f.write(summary)

        sys.exit(1)
    except Exception as e:
        print(f"❌ 验证过程中出现错误: {e!s}")
        sys.exit(1)


def main() -> None:
    """主函数"""
    os.getenv("IS_COMMIT", "false").lower() == "true"
    is_revalidate = os.getenv("IS_REVALIDATE", "false").lower() == "true"

    if is_revalidate:
        handle_toggle()
    else:
        try:
            validate_submission()
            # 设置 GitHub Actions 输出
            github_output = os.getenv("GITHUB_OUTPUT")
            if github_output:
                with open(github_output, "a", encoding="utf-8") as f:
                    if Path("artifacts/validation_result.json").exists():
                        f.write("needs_repo_check=true\n")
                    else:
                        f.write("needs_repo_check=false\n")
            else:
                if Path("artifacts/validation_result.json").exists():
                    print("::set-output name=needs_repo_check::true")
                else:
                    print("::set-output name=needs_repo_check::false")
        except SystemExit:
            github_output = os.getenv("GITHUB_OUTPUT")
            if github_output:
                with open(github_output, "a", encoding="utf-8") as f:
                    f.write("needs_repo_check=false\n")
            else:
                print("::set-output name=needs_repo_check::false")
            raise


if __name__ == "__main__":
    main()
