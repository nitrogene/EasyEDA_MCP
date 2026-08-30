import asyncio
import json
import socket
import sys

# Ensure UTF-8 output for Windows console/stderr
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import uuid
import websockets
from mcp.server import Server
from mcp.types import Tool, TextContent

WS_HOST = "127.0.0.1"
WS_PORT = 8787

easyeda_ws = None
pending_requests = {}


def is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            s.connect((host, port))
            return True
        except (ConnectionRefusedError, OSError, TimeoutError):
            return False

app = Server("EasyEDA_Local_MCP")

async def ws_handler(websocket):
    global easyeda_ws
    print("✅ EasyEDA connected to local MCP!", file=sys.stderr)
    easyeda_ws = websocket
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                event = data.get("event", "")
                body = json.loads(data.get("body", "{}"))

                if event == "pong":
                    continue

                if event.endswith(":result"):
                    msg_id = body.get("id")
                    if msg_id and msg_id in pending_requests:
                        pending_requests[msg_id].set_result(body)
                    continue

                if event == "ping":
                    await websocket.send(json.dumps({
                        "event": "pong",
                        "body": "{}"
                    }))
                    continue

            except Exception as e:
                print(f"WS Parse Error: {e}", file=sys.stderr)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        easyeda_ws = None
        for fut in pending_requests.values():
            if not fut.done():
                fut.set_exception(Exception("EasyEDA disconnected"))
        pending_requests.clear()
        print("❌ EasyEDA disconnected.", file=sys.stderr)

async def start_ws_server():
    async with websockets.serve(ws_handler, WS_HOST, WS_PORT):
        await asyncio.Future()

async def send_event(event_name: str, body: dict = {}, timeout: float = 10.0):
    global easyeda_ws
    if not easyeda_ws:
        raise Exception("EasyEDA is not connected")

    msg_id = str(uuid.uuid4())
    body["id"] = msg_id

    message = json.dumps({
        "event": event_name,
        "body": json.dumps(body)
    })

    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    pending_requests[msg_id] = fut

    try:
        await easyeda_ws.send(message)
        result = await asyncio.wait_for(fut, timeout=timeout)

        if result.get("ok"):
            return result.get("result")
        else:
            raise Exception(result.get("error", "Unknown error from EasyEDA"))
    except asyncio.TimeoutError:
        raise Exception("Timeout waiting for a response from EasyEDA")
    finally:
        pending_requests.pop(msg_id, None)

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_components",
            description="Get the list of IDs of all components on the current EasyEDA schematic",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_current_project_info",
            description="Get information about the currently open project (name, sheets, boards)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="open_document",
            description="Open a document (schematic/board) by its UUID",
            inputSchema={
                "type": "object",
                "properties": {
                    "uuid": {"type": "string", "description": "Document UUID"}
                },
                "required": ["uuid"]
            }
        ),
        Tool(
            name="create_schematic",
            description="Create a new schematic in the current project",
            inputSchema={
                "type": "object",
                "properties": {
                    "boardName": {"type": "string", "description": "Name for the new board/schematic (optional)"}
                }
            }
        ),
        Tool(
            name="create_schematic_page",
            description="Create a new page in an existing schematic",
            inputSchema={
                "type": "object",
                "properties": {
                    "schematicUuid": {"type": "string", "description": "Schematic UUID"}
                },
                "required": ["schematicUuid"]
            }
        ),
        Tool(
            name="modify_schematic_name",
            description="Rename a schematic",
            inputSchema={
                "type": "object",
                "properties": {
                    "schematicUuid": {"type": "string", "description": "Schematic UUID"},
                    "schematicName": {"type": "string", "description": "New name"}
                },
                "required": ["schematicUuid", "schematicName"]
            }
        ),
        Tool(
            name="modify_schematic_page_name",
            description="Rename a schematic page",
            inputSchema={
                "type": "object",
                "properties": {
                    "schematicPageUuid": {"type": "string", "description": "Page UUID"},
                    "schematicPageName": {"type": "string", "description": "New page name"}
                },
                "required": ["schematicPageUuid", "schematicPageName"]
            }
        ),
        Tool(
            name="execute_js",
            description=(
                "MAIN EasyEDA Pro CONTROL TOOL. "
                "AI ATTENTION: You are connected to the EasyEDA CAD environment. This tool allows you to execute arbitrary JS code inside the application. "
                "You have access to 676+ undocumented API commands (starting with eda.pcb_... or eda.sch_...). "
                "RULES FOR AI:\n"
                "1. If you don't know the required command, ALWAYS call `get_api_catalog` first to read the API reference.\n"
                "2. All API calls are asynchronous. You MUST use: `await eda.command_name()`.\n"
                "3. The script must return a value via `return`.\n"
                "4. To modify PCB objects (placement, layers), use `eda.pcb_PrimitiveComponent.modify(id, {x, y, layerid: 2})` (layerid 1=Top, 2=Bottom).\n"
                "5. Write smart JS macros (loops, filtering) directly inside this tool to avoid calling the API for single items one by one."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "JavaScript code. Example: return await eda.sch_PrimitiveComponent.getAllPrimitiveId();"}
                },
                "required": ["script"]
            }
        ),
        Tool(
            name="get_api_catalog",
            description=(
                "API KNOWLEDGE BASE: Get the complete catalog of available EasyEDA Pro API commands. "
                "MANDATORY: Use this tool at the start of a session or when searching for a specific function "
                "to learn the exact syntax (e.g. sch_Document, pcb_PrimitiveComponent, etc.), "
                "and then execute the discovered functions via the execute_js tool."
            ),
            inputSchema={"type": "object", "properties": {}}
        )
    ]

TOOL_TO_EVENT = {
    "get_components": "get-schematic",
    "get_current_project_info": "get-current-project-info",
    "open_document": "open-document",
    "create_schematic": "create-schematic",
    "create_schematic_page": "create-schematic-page",
    "modify_schematic_name": "modify-schematic-name",
    "modify_schematic_page_name": "modify-schematic-page-name",
    "execute_js": "execute-js",
    "get_api_catalog": "get-api-catalog",
}

TOOL_ARGS_MAP = {
    "open_document": lambda args: {"documentUuid": args.get("uuid")},
    "execute_js": lambda args: {"script": args.get("script")},
}

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if not easyeda_ws:
        return [TextContent(type="text", text="Error: EasyEDA is not connected. Open the application and activate the plugin.")]

    event_name = TOOL_TO_EVENT.get(name)
    if not event_name:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    if name in TOOL_ARGS_MAP:
        body = TOOL_ARGS_MAP[name](arguments)
    else:
        body = dict(arguments)

    try:
        result = await send_event(event_name, body)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    if is_port_in_use(WS_HOST, WS_PORT):
        print(
            f"❌ Port {WS_PORT} is already in use! Another instance of EasyEDA MCP "
            f"is already running. Shutting down.",
            file=sys.stderr
        )
        sys.exit(1)

    ws_task = asyncio.create_task(start_ws_server())

    def _on_ws_done(task: asyncio.Task):
        if task.cancelled():
            return
        exc = task.exception()
        if exc:
            print(f"❌ WebSocket server crashed: {exc}", file=sys.stderr)
            asyncio.get_event_loop().stop()

    ws_task.add_done_callback(_on_ws_done)

    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())