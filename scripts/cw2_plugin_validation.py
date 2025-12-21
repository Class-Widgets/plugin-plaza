#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path
from typing import Any

import requests
from cw2_models import CW2ManifestItem, CW2Submission
from pydantic import ValidationError


def fetch_cwplugin_json_from_repo(repo_url: str, branch: str = "main") -> dict[str, Any] | None:
    """从GitHub仓库获取cwplugin.json文件内容"""
    try:
        if not repo_url.startswith("https://github.com/"):
            return None
        repo_url = repo_url.rstrip("/")
        if repo_url.endswith(".git"):
            repo_url = repo_url[:-4]
        raw_url = repo_url.replace("https://github.com/", "https://raw.githubusercontent.com/")
        cwplugin_json_url = f"{raw_url}/{branch}/cwplugin.json"
        headers = {}
        github_token = os.environ.get("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        response = requests.get(cwplugin_json_url, headers=headers, timeout=10)
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


def validate_submission_metadata(data: dict[str, Any]) -> tuple[bool, list[str], CW2ManifestItem | None]:
    """验证提交的 Class Widgets 2 插件元数据"""
    errors = []

    try:
        submission = CW2Submission(**data)
        # 将逗号分隔的标签字符串拆分为列表
        tags_list = None
        if submission.tags:
            tags_list = [tag.strip() for tag in submission.tags.split(",") if tag.strip()]

        manifest_item = CW2ManifestItem(
            id=submission.id,
            name=submission.name,
            version=submission.version,
            api_version=submission.api_version,
            description=submission.description,
            author=submission.author,
            url=submission.url,
            branch=submission.branch,
            readme=submission.readme,
            icon=submission.icon,
            tags=tags_list,
        )

        return True, [], manifest_item

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
        with open(artifacts_dir / "cw2_comment.md", "w", encoding="utf-8") as f:
            f.write(comment)
        return
    cwplugin_json = fetch_cwplugin_json_from_repo(form_data["url"], form_data["branch"])
    if not cwplugin_json:
        comment = f"""<!-- plugin-review -->
❌ **Class Widgets 2 验证失败**

无法从仓库获取 `cwplugin.json` 文件:
- 仓库URL: `{form_data["url"]}`
- 请确保仓库是公开的且包含有效的 `cwplugin.json` 文件
"""

        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        with open(artifacts_dir / "cw2_comment.md", "w", encoding="utf-8") as f:
            f.write(comment)
        return
    merged_data = {
        "id": form_data["id"],
        "name": cwplugin_json.get("name", ""),
        "version": cwplugin_json.get("version", ""),
        "api_version": cwplugin_json.get("api_version", ""),
        "description": cwplugin_json.get("description", ""),
        "author": cwplugin_json.get("author", ""),
        "url": form_data["url"],
        "branch": form_data["branch"],
        "tags": form_data["tag"],
        "readme": cwplugin_json.get("readme", "README.md"),
        "icon": cwplugin_json.get("icon"),
    }

    success, errors, registry_item = validate_submission_metadata(merged_data)

    if success and registry_item:
        validation_result = {
            "success": True,
            "registry_item": registry_item.model_dump(),
            "plugin_id": form_data["id"],
            "form_data": form_data,
            "plugin_json": cwplugin_json,
        }

        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        with open(artifacts_dir / "cw2_validation_result.json", "w", encoding="utf-8") as f:
            json.dump(validation_result, f, indent=2, ensure_ascii=False)

        # 创建提交标志文件
        with open(artifacts_dir / "commit.flag", "w") as f:
            f.write("true")
        formatted_json = json.dumps(registry_item.model_dump(), indent=2, ensure_ascii=False)
        comment = f"""<!-- plugin-review -->
✅ **Class Widgets 2 验证通过**

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
"""
    else:
        validation_result = {"success": False, "errors": errors, "form_data": form_data, "plugin_json": cwplugin_json}
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        with open(artifacts_dir / "cw2_validation_result.json", "w", encoding="utf-8") as f:
            json.dump(validation_result, f, indent=2, ensure_ascii=False)
        error_text = "\n".join(f"- {error}" for error in errors)
        comment = f"""<!-- plugin-review -->
❌ **Class Widgets 2 验证失败**

**错误信息:**
{error_text}

**获取到的cwplugin.json内容:**
```json
{json.dumps(cwplugin_json, indent=2, ensure_ascii=False)}
```
"""

    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    with open(artifacts_dir / "cw2_comment.md", "w", encoding="utf-8") as f:
        f.write(comment)


def main() -> None:
    """主函数"""
    try:
        validate_submission()

        # 设置 GitHub Actions 输出
        github_output = os.getenv("GITHUB_OUTPUT")
        result_file = Path("artifacts/cw2_validation_result.json")

        if result_file.exists():
            try:
                with open(result_file, encoding="utf-8") as f:
                    result_data = json.load(f)
                    needs_repo_check = "true" if result_data.get("success", False) else "false"
            except Exception:
                needs_repo_check = "false"
        else:
            needs_repo_check = "false"

        if github_output:
            with open(github_output, "a", encoding="utf-8") as f:
                f.write(f"needs_repo_check={needs_repo_check}\n")
        else:
            print(f"::set-output name=needs_repo_check::{needs_repo_check}")

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
