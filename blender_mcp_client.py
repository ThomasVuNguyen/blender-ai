"""Small CLI for this workspace's Blender MCP connection.

Run with: uv run --with mcp-for-blender python blender_mcp_client.py scene
"""

import argparse
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run(command: str, path: Path | None, prompt: str) -> int:
    server = StdioServerParameters(
        command=str(Path.home() / ".local/bin/uvx"),
        args=["mcp-for-blender"],
    )
    # The server logs the entire submitted script. Keep it out of the agent's
    # tool output while retaining the latest log for connection diagnostics.
    log_path = Path(__file__).resolve().parent / "blender-mcp-client.log"
    with log_path.open("w") as server_log:
        async with stdio_client(server, errlog=server_log) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                if command == "tools":
                    for tool in (await session.list_tools()).tools:
                        print(tool.name)
                    return 0
                if command == "scene":
                    result = await session.call_tool("get_scene_info", {})
                else:
                    assert path is not None
                    source = path.resolve().read_text()
                    code = f"exec(compile({source!r}, {str(path)!r}, 'exec'))"
                    result = await session.call_tool(
                        "execute_blender_code", {"code": code, "user_prompt": prompt}
                    )
                messages = [str(getattr(part, "text", part)) for part in result.content]
                for message in messages:
                    print(message)
                # This add-on has returned an execution exception in text with
                # isError=False, so inspect both signals.
                failed = result.isError or any(
                    message.startswith("Error executing code:") for message in messages
                )
                return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("tools", "scene", "exec"))
    parser.add_argument("path", type=Path, nargs="?")
    parser.add_argument("--prompt", default="Run the Blender scene script.")
    args = parser.parse_args()
    if args.command == "exec" and args.path is None:
        parser.error("exec requires a Python script path")
    if args.command != "exec" and args.path is not None:
        parser.error("only exec accepts a script path")
    return asyncio.run(run(args.command, args.path, args.prompt))


if __name__ == "__main__":
    sys.exit(main())
