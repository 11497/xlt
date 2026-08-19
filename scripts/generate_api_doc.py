"""
根据 FastAPI OpenAPI 架构生成 Markdown 接口文档。
"""

from __future__ import annotations

import sys
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "接口文档.md"

# 直接运行脚本时，确保可以导入项目入口 `main.py` 及其依赖包。
sys.path.insert(0, str(PROJECT_ROOT))

from main import app  # noqa: E402


HTTP_METHODS = ("get", "post", "put", "patch", "delete", "options", "head")


def table_cell(value: Any) -> str:
    """转义 Markdown 表格单元格中的特殊字符。"""
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def schema_description(schema: dict[str, Any]) -> str:
    """返回 JSON Schema 片段的简洁可读描述。"""
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if "anyOf" in schema:
        return " | ".join(schema_description(item) for item in schema["anyOf"])
    if "oneOf" in schema:
        return " | ".join(schema_description(item) for item in schema["oneOf"])
    if "allOf" in schema:
        return " & ".join(schema_description(item) for item in schema["allOf"])

    schema_type = schema.get("type", "object")
    if schema_type == "array":
        return f"数组<{schema_description(schema.get('items', {}))}>"
    if "enum" in schema:
        return f"{schema_type}: {', '.join(map(str, schema['enum']))}"
    return schema_type


def extract_docstring_sections(description: str) -> tuple[str, list[tuple[str, str]], str]:
    """从路由说明中提取 :param 和 :return: 文档标记。"""
    parameters = re.findall(r"^:param\s+([^:]+):\s*(.*)$", description, flags=re.MULTILINE)
    returns = re.findall(r"^:return:\s*(.*)$", description, flags=re.MULTILINE)
    plain_description = re.sub(r"^:(?:param\s+[^:]+|return):.*$", "", description, flags=re.MULTILINE)
    plain_description = "\n".join(line for line in plain_description.splitlines() if line.strip()).strip()
    return plain_description, parameters, " ".join(returns).strip()


def render_docstring_parameters(parameters: list[tuple[str, str]]) -> list[str]:
    if not parameters:
        return []

    lines = ["##### 参数说明", "", "| 参数 | 说明 |", "| --- | --- |"]
    for name, description in parameters:
        escaped_description = table_cell(description.strip())
        lines.append(f"| `{name.strip()}` | {escaped_description} |")
    return lines


def render_docstring_return(return_description: str) -> list[str]:
    if not return_description:
        return []

    escaped_description = table_cell(return_description)
    return [
        "##### 返回说明",
        "",
        "| 返回值 | 说明 |",
        "| --- | --- |",
        f"| `data` | {escaped_description} |",
    ]


def render_parameters(parameters: list[dict[str, Any]]) -> list[str]:
    if not parameters:
        return []

    lines = ["##### 参数", "", "| 名称 | 位置 | 必填 | 类型 | 说明 |", "| --- | --- | --- | --- | --- |"]
    for parameter in parameters:
        schema = parameter.get("schema", {})
        required = "是" if parameter.get("required", False) else "否"
        description = table_cell(parameter.get("description", ""))
        lines.append(
            f"| `{parameter['name']}` | {parameter.get('in', '')} | {required} | "
            f"{table_cell(schema_description(schema))} | {description} |"
        )
    return lines


def resolve_schema(schema: dict[str, Any], component_schemas: dict[str, Any]) -> dict[str, Any]:
    """解析指向 OpenAPI 组件模型的引用。"""
    reference = schema.get("$ref")
    if not reference:
        return schema
    return component_schemas.get(reference.rsplit("/", 1)[-1], schema)


def schema_details(schema: dict[str, Any]) -> str:
    """整理模型字段的约束和说明。"""
    details = []
    for key in ("minLength", "maxLength", "minimum", "maximum", "default", "description"):
        if key in schema:
            details.append(f"{key}={schema[key]}")
    return ", ".join(details)


def render_request_body(request_body: dict[str, Any] | None, component_schemas: dict[str, Any]) -> list[str]:
    if not request_body:
        return []

    lines = ["##### 请求体", ""]
    body_required = "是" if request_body.get("required", False) else "否"
    description = request_body.get("description", "")
    if description:
        lines.extend([description, ""])
    lines.extend([
        "| 内容类型 | 请求体必填 | 字段 | 字段必填 | 类型 | 约束 / 说明 |",
        "| --- | --- | --- | --- | --- | --- |",
    ])
    for content_type, content in request_body.get("content", {}).items():
        schema = content.get("schema", {})
        resolved_schema = resolve_schema(schema, component_schemas)
        properties = resolved_schema.get("properties", {})
        required_fields = set(resolved_schema.get("required", []))
        if not properties:
            lines.append(
                f"| `{content_type}` | {body_required} | - | - | "
                f"{table_cell(schema_description(schema))} | - |"
            )
            continue

        for field_name, field_schema in properties.items():
            field_required = "是" if field_name in required_fields else "否"
            lines.append(
                f"| `{content_type}` | {body_required} | `{field_name}` | {field_required} | "
                f"{table_cell(schema_description(field_schema))} | {table_cell(schema_details(field_schema))} |"
            )
    return lines


def render_responses(responses: dict[str, Any]) -> list[str]:
    lines = ["##### 响应", "", "| 状态码 | 说明 | 数据模型 |", "| --- | --- | --- |"]
    for status, response in responses.items():
        content = response.get("content", {})
        schemas = [schema_description(value.get("schema", {})) for value in content.values()]
        description = table_cell(response.get("description", ""))
        lines.append(
            f"| {status} | {description} | "
            f"{table_cell(', '.join(schemas))} |"
        )
    return lines


def render_components(openapi_schema: dict[str, Any]) -> list[str]:
    schemas = openapi_schema.get("components", {}).get("schemas", {})
    if not schemas:
        return []

    lines = ["## 数据模型", ""]
    for name, schema in schemas.items():
        lines.extend([f"### {name}", ""])
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        if not properties:
            lines.extend([f"`{schema_description(schema)}`", ""])
            continue

        lines.extend(["| 字段 | 必填 | 类型 | 约束 / 说明 |", "| --- | --- | --- | --- |"])
        for field_name, field_schema in properties.items():
            lines.append(
                f"| `{field_name}` | {'是' if field_name in required else '否'} | "
                f"{table_cell(schema_description(field_schema))} | {table_cell(schema_details(field_schema))} |"
            )
        lines.append("")
    return lines


def build_markdown(openapi_schema: dict[str, Any]) -> str:
    info = openapi_schema.get("info", {})
    component_schemas = openapi_schema.get("components", {}).get("schemas", {})
    lines = [
        f"# {info.get('title', '接口文档')}",
        "",
        f"OpenAPI 版本：`{openapi_schema.get('openapi', '')}`",
        "",
        "本文档由 `scripts/generate_api_doc.py` 自动生成，请勿手动编辑。",
        "",
        "## 接口列表",
        "",
    ]

    operations_by_tag: dict[str, list[tuple[str, str, dict[str, Any], dict[str, Any]]]] = {}
    for path, path_item in openapi_schema.get("paths", {}).items():
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not operation:
                continue

            # 一个接口可以有多个标签，因此会分别列在对应的标签章节中。
            for tag in operation.get("tags") or ["未分类"]:
                operations_by_tag.setdefault(tag, []).append((path, method, path_item, operation))

    for tag_index, (tag, tagged_operations) in enumerate(operations_by_tag.items(), start=1):
        lines.extend([f"### {tag_index}. {tag}", ""])
        for operation_index, (path, method, path_item, operation) in enumerate(tagged_operations, start=1):
            title = operation.get("summary") or operation.get("operationId", "")
            lines.extend([f"#### {tag_index}.{operation_index} `{method.upper()}` {path}", ""])
            if title:
                lines.extend([title, ""])
            description, docstring_parameters, return_description = extract_docstring_sections(
                operation.get("description", "")
            )
            if description:
                lines.extend([description, ""])
            lines.extend(render_docstring_parameters(docstring_parameters))
            if docstring_parameters:
                lines.append("")
            lines.extend(render_docstring_return(return_description))
            if return_description:
                lines.append("")
            lines.extend(render_parameters(path_item.get("parameters", []) + operation.get("parameters", [])))
            if operation.get("parameters") or path_item.get("parameters"):
                lines.append("")
            lines.extend(render_request_body(operation.get("requestBody"), component_schemas))
            if operation.get("requestBody"):
                lines.append("")
            lines.extend(render_responses(operation.get("responses", {})))
            lines.append("")

    lines.extend(render_components(openapi_schema))
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    # FastAPI 会将所有已注册的路由汇总为此 OpenAPI 架构。
    openapi_schema = app.openapi()
    OUTPUT_FILE.write_text(build_markdown(openapi_schema), encoding="utf-8")
    print(f"已生成 {OUTPUT_FILE.relative_to(PROJECT_ROOT)}，共包含 {len(openapi_schema['paths'])} 条路径。")


if __name__ == "__main__":
    main()
