import json
import os
import sys
from pathlib import Path
from subprocess import TimeoutExpired, run

from models import PluginJson
from pydantic import ValidationError


def check_python_files(repo_dir: Path) -> tuple[bool, list[str]]:
    """递归查找所有 .py 文件并进行编译检查"""
    errors: list[str] = []
    ok = True

    try:
        py_files = list[Path](repo_dir.rglob("*.py"))
        if not py_files:
            errors.append("未找到任何Python文件")
            return False, errors

        print(f"找到 {len(py_files)} 个Python文件, 开始检查...")

        for py_file in py_files:
            try:
                result = run(
                    ["python", "-m", "py_compile", str(py_file)],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=30,  # 30秒超时
                )

                if result.returncode != 0:
                    ok = False
                    error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
                    relative_path = py_file.relative_to(repo_dir)
                    errors.append(f"{relative_path}: {error_msg}")
                    print(f"[ERROR] {relative_path}: 编译失败")
                else:
                    relative_path = py_file.relative_to(repo_dir)
                    print(f"[OK] {relative_path}: 编译通过")

            except TimeoutExpired:
                ok = False
                relative_path = py_file.relative_to(repo_dir)
                errors.append(f"{relative_path}: 编译超时")
                print(f"[TIMEOUT] {relative_path}: 编译超时")
            except Exception as e:
                ok = False
                relative_path = py_file.relative_to(repo_dir)
                errors.append(f"{relative_path}: 检查异常 - {e!s}")
                print(f"[EXCEPTION] {relative_path}: 检查异常 - {e!s}")

    except Exception as e:
        ok = False
        errors.append(f"执行Python文件检查时出现异常: {e!s}")
        print(f"执行Python文件检查时出现异常: {e!s}")

    return ok, errors


def check_plugin_json(repo_dir: Path) -> tuple[bool, list[str], dict]:
    """检查plugin.json文件"""
    errors: list[str] = []
    plugin_json_data = {}

    plugin_json_path = repo_dir / "plugin.json"
    if not plugin_json_path.exists():
        errors.append("未找到plugin.json文件")
        return False, errors, plugin_json_data

    try:
        with open(plugin_json_path, encoding="utf-8") as f:
            plugin_json_data = json.load(f)
        try:
            PluginJson(**plugin_json_data)
            print("[OK] plugin.json: 格式检查通过")
            return True, errors, plugin_json_data
        except ValidationError as e:
            for error in e.errors():
                field = error.get("loc", ["unknown"])[0]
                msg = error.get("msg", "validation error")
                errors.append(f"plugin.json字段 '{field}' 验证失败: {msg}")
            return False, errors, plugin_json_data

    except json.JSONDecodeError as e:
        errors.append(f"plugin.json格式错误: {e!s}")
        return False, errors, plugin_json_data
    except Exception as e:
        errors.append(f"读取plugin.json时出现错误: {e!s}")
        return False, errors, plugin_json_data


def build_check_result_comment(
    py_ok: bool, py_errors: list[str], json_ok: bool, json_errors: list[str], plugin_json_data: dict
) -> str:
    """构建检查结果评论"""
    if py_ok:
        py_section = "[OK] **Python文件 编译检查通过**"
    else:
        py_error_text = "\n".join(f"- {err}" for err in py_errors)
        py_section = f"[ERROR] **Python文件 编译检查失败**\n\n{py_error_text}"
    if json_ok:
        formatted_json = json.dumps(plugin_json_data, indent=2, ensure_ascii=False)
        json_section = f"[OK] **plugin.json 检查通过**\n\n```json\n{formatted_json}\n```"
    else:
        json_error_text = "\n".join(f"- {err}" for err in json_errors)
        json_section = f"[ERROR] **plugin.json 检查失败**\n\n{json_error_text}"

    overall_status = "[OK] **仓库检查通过**" if (py_ok and json_ok) else "[ERROR] **仓库检查失败**"

    return f"""{overall_status}

## Python文件检查
{py_section}

## plugin.json检查
{json_section}

---
> 仓库检查完成"""


def main():
    repo_dir = Path(os.getenv("REPO_DIR", ".")).resolve()
    if not repo_dir.exists():
        print(f"[ERROR] 仓库目录不存在: {repo_dir}")
        sys.exit(1)
    print(f"检查仓库: {repo_dir}")
    py_ok, py_errors = check_python_files(repo_dir)
    json_ok, json_errors, plugin_json_data = check_plugin_json(repo_dir)
    overall_ok = py_ok and json_ok
    comment = build_check_result_comment(py_ok, py_errors, json_ok, json_errors, plugin_json_data)
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    with open(artifacts_dir / "repo_check_comment.md", "w", encoding="utf-8") as f:
        f.write(comment)
    result_data = {
        "success": overall_ok,
        "python_check": {"success": py_ok, "errors": py_errors},
        "plugin_json_check": {"success": json_ok, "errors": json_errors, "data": plugin_json_data},
    }
    with open(artifacts_dir / "repo_check_result.json", "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    print(f"repo_check_success={str(overall_ok).lower()}")
    print(f"python_check_success={str(py_ok).lower()}")
    print(f"plugin_json_check_success={str(json_ok).lower()}")
    if overall_ok:
        print("[SUCCESS] 仓库检查通过!")
    else:
        print("[ERROR] 仓库检查发现问题")
        if not py_ok:
            print(f"Python文件问题: {len(py_errors)} 个")
        if not json_ok:
            print(f"plugin.json问题: {len(json_errors)} 个")

    if not overall_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
