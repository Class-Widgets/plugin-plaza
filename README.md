# 插件广场 (Plugin Plaza)
存储插件索引、Banner、介绍等信息。

## 如何使用
> [!TIP]
> 教程正在制作中，敬请期待！

## 发布插件
> [!Note]
> 请确保在您的插件的 GitHub 仓库中至少发布了一个 Release（您只需将插件打包成 .zip 压缩包上传），否则插件将无法在 PluginPlaza 中下载。

若要发布插件，请按以下步骤操作：

1. Fork 本项目。
2. 修改 `./Plugins/plugin_list.json` 文件，按照以下格式添加您的插件信息，随后提交PR 等待审核即可。

插件信息格式如下：
```
{
    "其他插件...": {
        ...
    },
    // 在这里添加您的插件信息
    "您的插件仓库名称": {
        "name": "插件在 PluginPlaza 显示的名称",
        "description": "插件的简介",
        "version": "插件版本号（如：1.0.0）",
        "plugin_ver": "插件支持的 Class Widgets 版本号（可在 Class Widgets 的 config.ini 中的 [Plugin] 部分找到该值）",
        "author": "插件作者的 PluginPlaza 名称",
    
        "url": "您的 GitHub 插件仓库链接 (例如：https://github.com/RinLit-233-shiroko/cw-example-plugin)",
        "branch": "插件仓库的分支（如：main）",
    
        "update_date": "插件更新日期（格式：yyyy/mm/dd）",
    
        "tag": "插件标签"
    }
}
```

后续更新时，您只需修改仓库中的 `plugin.json` 文件，更新版本号（`version`）和更新时间（`update_date`）。本仓库的脚本会每半小时自动检测插件更新。（更新脚本只检测版本号及时间的更新 如果有其他更变 请重新提交PR）
