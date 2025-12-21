#!/usr/bin/env python3
"""
Plugin Manifest Index Generator

自动扫描manifest目录中的所有插件配置文件，
生成结构化的插件索引文件。
"""

import argparse
import glob
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class PluginIndexGenerator:
    """插件索引生成器"""

    def __init__(self, manifest_dir: str, output_file: Optional[str] = None):
        """
        初始化索引生成器

        Args:
            manifest_dir: manifest目录路径
            output_file: 输出文件路径，默认为manifest_dir/../index.json (plugins文件夹下)
        """
        self.manifest_dir = Path(manifest_dir).resolve()
        if output_file:
            self.output_file = Path(output_file)
        else:
            # 默认输出到manifest目录的父目录(plugins文件夹)下
            self.output_file = self.manifest_dir.parent / "index.json"
        self.plugins: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, str]] = []

    def scan_manifest_files(self) -> List[Path]:
        """
        扫描manifest目录中的所有JSON文件

        Returns:
            JSON文件路径列表
        """
        json_files = glob.glob(str(self.manifest_dir / "*.json"))
        return [Path(f) for f in json_files]

    def parse_plugin_manifest(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        解析单个插件manifest文件

        Args:
            file_path: JSON文件路径

        Returns:
            解析后的插件信息字典，解析失败返回None
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # 验证必需的字段
            required_fields = ["id", "name", "version"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                self.errors.append(
                    {"file": str(file_path), "error": f"Missing required fields: {', '.join(missing_fields)}"}
                )
                return None

            # 添加文件信息
            data["_file_path"] = str(file_path.relative_to(self.manifest_dir))
            data["_file_size"] = file_path.stat().st_size
            data["_modified_time"] = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()

            return data

        except json.JSONDecodeError as e:
            self.errors.append({"file": str(file_path), "error": f"Invalid JSON: {e!s}"})
            return None
        except Exception as e:
            self.errors.append({"file": str(file_path), "error": f"File read error: {e!s}"})
            return None

    def generate_statistics(self) -> Dict[str, Any]:
        """
        生成插件统计信息

        Returns:
            统计信息字典
        """
        if not self.plugins:
            return {
                "total_plugins": 0,
                "total_errors": len(self.errors),
                "unique_authors": [],
                "version_distribution": {},
                "tag_distribution": {},
            }

        # 统计作者
        authors = set()
        version_dist = {}
        tag_dist = {}

        for plugin in self.plugins:
            # 作者统计
            author = plugin.get("author", "Unknown")
            authors.add(author)

            # 版本分布
            version = plugin.get("version", "unknown")
            version_dist[version] = version_dist.get(version, 0) + 1

            # 标签分布
            tags = plugin.get("tags", [])
            for tag in tags:
                tag_dist[tag] = tag_dist.get(tag, 0) + 1

        return {
            "total_plugins": len(self.plugins),
            "total_errors": len(self.errors),
            "unique_authors": sorted(authors),
            "version_distribution": dict(sorted(version_dist.items())),
            "tag_distribution": dict(sorted(tag_dist.items(), key=lambda x: x[1], reverse=True)),
        }

    def generate_index(self) -> Dict[str, Any]:
        """
        生成完整的插件索引

        Returns:
            索引字典
        """
        # 扫描文件
        json_files = self.scan_manifest_files()

        # 解析每个文件
        for file_path in json_files:
            plugin_data = self.parse_plugin_manifest(file_path)
            if plugin_data:
                self.plugins.append(plugin_data)

        # 按插件ID排序
        self.plugins.sort(key=lambda x: x.get("id", ""))

        # 生成统计信息
        statistics = self.generate_statistics()

        # 构建索引
        index = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "manifest_directory": str(self.manifest_dir),
                "total_files_scanned": len(json_files),
                "generator_version": "1.0.0",
            },
            "statistics": statistics,
            "plugins": self.plugins,
            "errors": self.errors,
        }

        return index

    def save_index(self, index: Dict[str, Any]) -> bool:
        """
        保存索引到文件

        Args:
            index: 索引字典

        Returns:
            保存是否成功
        """
        try:
            # 确保输出目录存在
            self.output_file.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2, ensure_ascii=False)

            print(f"✅ 索引已生成: {self.output_file}")
            print(f"📊 插件数量: {index['statistics']['total_plugins']}")
            print(f"⚠️  错误数量: {index['statistics']['total_errors']}")

            return True

        except Exception as e:
            print(f"❌ 保存索引失败: {e!s}")
            return False

    def generate(self) -> bool:
        """
        执行完整的索引生成流程

        Returns:
            生成是否成功
        """
        print(f"🔍 扫描目录: {self.manifest_dir}")

        if not self.manifest_dir.exists():
            print(f"❌ 目录不存在: {self.manifest_dir}")
            return False

        if not self.manifest_dir.is_dir():
            print(f"❌ 不是有效目录: {self.manifest_dir}")
            return False

        # 生成索引
        index = self.generate_index()

        # 保存索引
        return self.save_index(index)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Plugin Manifest Index Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s                                    # 生成当前目录的索引
  %(prog)s /path/to/manifest                  # 指定manifest目录
  %(prog)s -o /path/to/output.json           # 指定输出文件
  %(prog)s --manifest-dir /path/to/manifest --output /path/to/index.json
        """,
    )

    parser.add_argument(
        "manifest_dir", nargs="?", default=".", help="Plugin manifest directory (default: current directory)"
    )

    parser.add_argument("-o", "--output", help="Output index file path (default: manifest_dir/index.json)")

    parser.add_argument("--version", action="version", version="Plugin Index Generator 1.0.0")

    args = parser.parse_args()

    # 创建生成器并执行
    generator = PluginIndexGenerator(args.manifest_dir, args.output)
    success = generator.generate()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
