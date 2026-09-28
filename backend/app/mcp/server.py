from .tools import invoke_tool, list_tools


def get_registered_tools() -> list[dict]:
    return list_tools()


def call_tool(name: str, arguments: dict) -> dict:
    return invoke_tool(name, arguments)
