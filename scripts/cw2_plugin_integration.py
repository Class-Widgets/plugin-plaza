import json
import os
import sys
from pathlib import Path

def create_manifest_files():
    """创建manifest文件并准备提交"""
    # 检查验证结果文件是否存在
    validation_result_path = Path("validation-artifacts/cw2_validation_result.json")
    if not validation_result_path.exists():
        print("❌ Validation result file not found", file=sys.stderr)
        sys.exit(1)
    
    try:
        # 读取验证结果
        with open(validation_result_path, "r", encoding="utf-8") as f:
            validation_data = json.load(f)
        
        # 提取必要数据
        plugin_id = validation_data.get("plugin_id")
        registry_data = validation_data.get("registry_item")
        
        if not plugin_id or not registry_data:
            print("❌ Invalid validation result data", file=sys.stderr)
            sys.exit(1)
        
        # 创建manifest目录
        manifest_dir = Path("ClassWidgets2/plugins/manifest")
        manifest_dir.mkdir(exist_ok=True, parents=True)
        
        # 创建manifest文件
        manifest_file_path = manifest_dir / f"{plugin_id}.json"
        with open(manifest_file_path, "w", encoding="utf-8") as f:
            json.dump(registry_data, f, indent=2, ensure_ascii=False)
        
        # 创建artifacts目录
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        
        # 创建提交标志文件
        with open(artifacts_dir / "commit.flag", "w") as f:
            f.write("true")
        
        # 创建插件添加信息文件
        plugin_to_add = {plugin_id: registry_data}
        with open(artifacts_dir / "cw2_plugin_to_add.json", "w", encoding="utf-8") as f:
            json.dump(plugin_to_add, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created manifest file for plugin: {plugin_id}")
        print(f"✅ Created commit flag and plugin add information")
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON format in validation result", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    create_manifest_files()
