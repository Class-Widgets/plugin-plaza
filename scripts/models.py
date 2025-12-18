#!/usr/bin/env python3
from pydantic import BaseModel, Field, RootModel, field_validator, model_validator

GITHUB_URL_RE = r"^https://github.com/[\w.-]+/[\w.-]+/?$"
BRANCH_RE = r"^[A-Za-z0-9._\-/]+$"


class Submission(BaseModel):
    """提交的插件元数据格式"""

    id: str
    name: str
    version: str
    plugin_ver: int | str
    author: str
    url: str
    branch: str
    tag: str
    description: str | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL必须以http://或https://开头")
        return v


class PluginJson(BaseModel):
    """仓库中plugin.json的格式"""

    name: str
    version: str
    plugin_ver: int | str
    author: str
    url: str = Field(pattern=GITHUB_URL_RE)
    branch: str = Field(pattern=BRANCH_RE)
    update_date: str
    settings: bool | None = None
    description: str | None = None


class RegistryItem(BaseModel):
    """注册表中单个插件项的格式"""

    name: str
    version: str
    plugin_ver: int | str
    author: str
    url: str = Field(pattern=GITHUB_URL_RE)
    branch: str = Field(pattern=BRANCH_RE)
    tag: str
    description: str | None = None
    update_date: str | None = None


class RegistryItemWithId(RegistryItem):
    """带有 id 字段的注册表项, 用于验证"""

    id: str


class Registry(RootModel):
    """完整注册表格式"""

    root: dict[str, RegistryItem]

    @model_validator(mode="before")
    @classmethod
    def validate_items(cls, data):
        """将 JSON 键名作为 id 传递"""
        if isinstance(data, dict):
            validated_data = {}
            for plugin_id, plugin_data in data.items():
                if isinstance(plugin_data, dict):
                    temp_data = plugin_data.copy()
                    temp_data["id"] = plugin_id
                    RegistryItemWithId.model_validate(temp_data)
                    validated_data[plugin_id] = plugin_data
                else:
                    validated_data[plugin_id] = plugin_data
            return validated_data
        return data
