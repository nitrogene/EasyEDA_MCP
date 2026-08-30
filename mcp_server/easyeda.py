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
from mcp.server.mcpserver import MCPServer

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

app = MCPServer("EasyEDA_Local_MCP")

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

async def send_event(event_name: str, body: dict = None, timeout: float = 10.0):
    global easyeda_ws
    if body is None:
        body = {}
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


async def _run_tool(event_name: str, body: dict) -> str:
    """Shared helper: send the event to EasyEDA and format the result/error as text,
    matching the behavior of the original call_tool()."""
    if not easyeda_ws:
        return "Error: EasyEDA is not connected. Open the application and activate the plugin."
    try:
        result = await send_event(event_name, body)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return f"Error: {str(e)}"


@app.tool(description="Get the list of IDs of all components on the current EasyEDA schematic")
async def get_components() -> str:
    return await _run_tool("get-schematic", {})


@app.tool(description="Get information about the currently open project (name, sheets, boards)")
async def get_current_project_info() -> str:
    return await _run_tool("get-current-project-info", {})


@app.tool(description="Open a document (schematic/board) by its UUID")
async def open_document(uuid: str) -> str:
    """
    Args:
        uuid: Document UUID
    """
    return await _run_tool("open-document", {"documentUuid": uuid})


@app.tool(description="Create a new schematic in the current project")
async def create_schematic(boardName: str = "") -> str:
    """
    Args:
        boardName: Name for the new board/schematic (optional)
    """
    body = {"boardName": boardName} if boardName else {}
    return await _run_tool("create-schematic", body)


@app.tool(description="Create a new page in an existing schematic")
async def create_schematic_page(schematicUuid: str) -> str:
    """
    Args:
        schematicUuid: Schematic UUID
    """
    return await _run_tool("create-schematic-page", {"schematicUuid": schematicUuid})


@app.tool(description="Rename a schematic")
async def modify_schematic_name(schematicUuid: str, schematicName: str) -> str:
    """
    Args:
        schematicUuid: Schematic UUID
        schematicName: New name
    """
    return await _run_tool("modify-schematic-name", {
        "schematicUuid": schematicUuid,
        "schematicName": schematicName,
    })


@app.tool(description="Rename a schematic page")
async def modify_schematic_page_name(schematicPageUuid: str, schematicPageName: str) -> str:
    """
    Args:
        schematicPageUuid: Page UUID
        schematicPageName: New page name
    """
    return await _run_tool("modify-schematic-page-name", {
        "schematicPageUuid": schematicPageUuid,
        "schematicPageName": schematicPageName,
    })


@app.tool(
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
    )
)
async def execute_js(script: str) -> str:
    """
    Args:
        script: JavaScript code. Example: return await eda.sch_PrimitiveComponent.getAllPrimitiveId();
    """
    return await _run_tool("execute-js", {"script": script})


@app.tool(
    description=(
        "API KNOWLEDGE BASE: Get the complete catalog of available EasyEDA Pro API commands. "
        "MANDATORY: Use this tool at the start of a session or when searching for a specific function "
        "to learn the exact syntax (e.g. sch_Document, pcb_PrimitiveComponent, etc.), "
        "and then execute the discovered functions via the execute_js tool."
    )
)
async def get_api_catalog() -> str:
    return await _run_tool("get-api-catalog", {})


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

    await app.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())
