from pydantic import BaseModel, Field, RootModel, field_validator, model_validator
import re

GITHUB_URL_RE = r"^https://github.com/[\w.-]+/[\w.-]+/?$"
BRANCH_RE = r"^[A-Za-z0-9._\-/]+$"
PLUGIN_ID_RE = r"^[a-z0-9][a-z0-9.-]*[a-z0-9]$"


class CW2PluginJson(BaseModel):
    """Class Widgets 2 仓库中cwplugin.json的格式"""

    id: str
    name: str
    version: str
    api_version: str
    description: str
    author: str
    url: str = Field(pattern=GITHUB_URL_RE)
    branch: str = Field(pattern=BRANCH_RE)
    readme: str = "README.md"
    icon: str | None = None
    tags: list[str] | None = None

    @field_validator("id")
    @classmethod
    def validate_plugin_id(cls, v: str) -> str:
        if not re.match(PLUGIN_ID_RE, v):
            raise ValueError("插件ID只能包含小写字母、数字、点和连字符，且不能以点或连字符开头/结尾")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL必须以http://或https://开头")
        return v


class CW2ManifestItem(BaseModel):
    """Class Widgets 2 清单中单个插件项的格式"""

    id: str
    name: str
    version: str
    api_version: str
    description: str
    author: str
    url: str = Field(pattern=GITHUB_URL_RE)
    branch: str = Field(pattern=BRANCH_RE)
    readme: str = "README.md"
    icon: str | None = None
    tags: list[str] | None = None

    @field_validator("id")
    @classmethod
    def validate_plugin_id(cls, v: str) -> str:
        if not re.match(PLUGIN_ID_RE, v):
            raise ValueError("插件ID只能包含小写字母、数字、点和连字符，且不能以点或连字符开头/结尾")
        return v


class CW2Submission(BaseModel):
    """提交的 Class Widgets 2 插件元数据格式"""

    id: str
    name: str
    version: str
    api_version: str
    description: str
    author: str
    url: str
    branch: str
    tags: str
    readme: str = "README.md"
    icon: str | None = None

    @field_validator("id")
    @classmethod
    def validate_plugin_id(cls, v: str) -> str:
        if not re.match(PLUGIN_ID_RE, v):
            raise ValueError("插件ID只能包含小写字母、数字、点和连字符，且不能以点或连字符开头/结尾")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL必须以http://或https://开头")
        return v


class CW2ManifestRegistry(RootModel):
    """Class Widgets 2 完整清单格式"""

    root: dict[str, CW2ManifestItem]

    @model_validator(mode="before")
    @classmethod
    def validate_items(cls, data):
        """验证清单中的所有插件项"""
        if isinstance(data, dict):
            validated_data = {}
            for plugin_id, plugin_data in data.items():
                if isinstance(plugin_data, dict):
                    temp_data = plugin_data.copy()
                    temp_data["id"] = plugin_id
                    CW2ManifestItem.model_validate(temp_data)
                    validated_data[plugin_id] = plugin_data
                else:
                    validated_data[plugin_id] = plugin_data
            return validated_data
        return data