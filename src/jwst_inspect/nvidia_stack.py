from __future__ import annotations

import importlib
import shutil
from pathlib import Path
from typing import Any

import yaml


DEFAULT_STACK_CONFIG = Path("configs/nvidia_stack.yaml")


def load_stack_config(path: Path | str = DEFAULT_STACK_CONFIG) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{config_path}: expected YAML mapping")
    return data


def _module_available(module_name: str) -> dict[str, Any]:
    try:
        importlib.import_module(module_name)
    except Exception as exc:
        return {"name": module_name, "available": False, "error": str(exc)}
    return {"name": module_name, "available": True}


def _command_available(command: str) -> dict[str, Any]:
    path = shutil.which(command)
    return {"name": command, "available": path is not None, "path": path}


def inspect_stack(config: dict[str, Any], role: str) -> dict[str, Any]:
    tools = config.get("tools", {})
    if not isinstance(tools, dict):
        raise ValueError("NVIDIA stack config tools must be a mapping")

    inspected: dict[str, Any] = {}
    role_errors: list[str] = []
    for tool_name, tool in tools.items():
        if not isinstance(tool, dict):
            continue
        roles = [str(item) for item in tool.get("roles", [])]
        applies_to_role = role in roles
        commands = [_command_available(str(command)) for command in tool.get("expected_commands", [])]
        modules = [_module_available(str(module)) for module in tool.get("expected_modules", [])]
        errors = [
            f"missing command {item['name']}"
            for item in commands
            if applies_to_role and not item["available"]
        ]
        errors.extend(
            f"missing module {item['name']}: {item.get('error', 'not available')}"
            for item in modules
            if applies_to_role and not item["available"]
        )
        if errors:
            role_errors.extend(f"{tool_name}: {error}" for error in errors)
        inspected[tool_name] = {
            "source": tool.get("source"),
            "applies_to_role": applies_to_role,
            "roles": roles,
            "commands": commands,
            "modules": modules,
            "status": "passed" if not errors else "failed",
            "errors": errors,
        }

    return {
        "role": role,
        "status": "passed" if not role_errors else "failed",
        "errors": role_errors,
        "tools": inspected,
        "runtime": config.get("runtime", {}),
        "container_defaults": config.get("container_defaults", {}),
    }


def validate_stack_report(report: dict[str, Any], require_role_tools: bool = True) -> list[str]:
    errors: list[str] = []
    stack = report.get("stack")
    if not isinstance(stack, dict):
        return ["missing stack report"]
    if require_role_tools and stack.get("status") != "passed":
        errors.extend(str(error) for error in stack.get("errors", []))
    return errors
