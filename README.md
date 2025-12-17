# 插件广场 (Plugin Plaza)

插件的索引仓库

## 如何使用

> [!TIP]
> Class Widgets 已有官方教程，
> 插件开发教程详见[此处](https://cw.rinlit.cn/docs-dev)。

### 部署插件到广场

我们提供了**两种方式**来部署您的插件:

####  方式一: Issue 模板提交

1. 确保您的插件仓库包含有效的 plugin.json 文件
2. 在 GitHub 仓库中发布至少一个 Release
3. [点击这里创建插件提交 Issue](../../issues/new?assignees=&labels=plugin-add&projects=&template=plugin-add.yml&title=%5BPlugin+Add%5D+%3C%E6%8F%92%E4%BB%B6ID%3E)
4. 填写插件信息并提交

####  方式二: PR 提交

1. Fork 本项目
2. 修改 ./Plugins/plugin_list.json 文件或创建新的 ClassWidgets2/plugins/manifest/插件ID.json 文件
3. 提交 Pull Request

##  插件信息格式

### 旧规范插件 (Legacy Plugins)

在 plugin_list.json 中, 添加插件信息格式如下:

`json
{
  "您的插件ID": {
    "name": "插件显示名称",
    "description": "插件简介",
    "version": "1.0.0",
    "plugin_ver": "支持的 Class Widgets 版本",
    "author": "作者名称",
    "url": "https://github.com/username/plugin-repo",  # 插件仓库的 URL
    "branch": "main",  # 插件仓库的分支
    "update_date": "2024/01/01",
    "tag": "实用 | 工具"  # 插件标签,多个标签用\ | \分"
  }
}
`

> [!IMPORTANT]
> **注意**：这里的格式与插件仓库中的 plugin.json 不同，请仔细检查格式。

### Class Widgets 2 插件 (CW2 Plugins)

在 ClassWidgets2/plugins/manifest/ 目录中, 每个插件都有自己的独立JSON文件, 格式如下:

`json
{
  "id": "您的插件ID",
  "name": "插件显示名称",
  "version": "1.0.0",
  "api_version": "1.0.0",  # 插件API版本
  "description": "插件简介",
  "author": "作者名称",
  "url": "https://github.com/username/plugin-repo",  # 插件仓库的 URL
  "branch": "main",  # 插件仓库的分支
  "readme": "README.md",  # 插件说明文件路径
  "icon": "icon.png",  # 插件图标路径
  "tags": ["实用", "工具"]  # 插件标签数组
}
`

> [!IMPORTANT]
> **注意**：对于 Class Widgets 2 插件，JSON 格式与插件仓库中的 plugin.json 保持一致，两套规范完全独立运行。

- **更新**：系统每 30 分钟自动检测插件更新，自动从您的 plugin.json 拉取版本号和更新时间

<div align="center">

如有疑问，请[创建 Issue](../../issues/new)或查看[官方文档](https://cw.rinlit.cn/docs-dev)

</div>
