# 🚀 EasyEDA Pro AI Automation Plugin & MCP Server

---

## English

Unlock the hidden potential of EasyEDA Pro! This plugin and MCP (Model Context Protocol) server turn your favorite AI (Claude, Antigravity, ChatGPT) into an expert PCB designer. Forget about endless manual clicking—simply ask the AI to route your board, align components, or assign 3D models.

By injecting a WebSocket bridge directly into the CAD environment, this tool exposes a massive arsenal of **over 670 undocumented internal API commands** to the AI.

### ✨ Magical Features

The plugin provides full "God-mode" access to the entire internal API of EasyEDA Pro. Here is a brief list of what the plugin can do programmatically:

- **Project & File Management:** Create, open, and rename projects, schematics, and PCBs. Read the entire structure of the current project.
- **Schematic (SCH) Operations:** Read absolutely everything: components, netlists, wires, and pins. Create, delete, and move schematic components. Programmatically draw wire connections. Modify any element properties (values, designators, attributes).
- **PCB Operations:**
  - **Placement:** Read coordinates of any elements and move/rotate them according to custom rules.
  - **Routing:** Draw tracks of any width on any layer, create vias, and pour copper.
  - **Board Management:** Edit the board outline, layers, and read DRC rules.
- **Full Customization:** The plugin can generate and execute any JavaScript macro on the fly directly inside the EasyEDA environment, automating any routine task that can be done with a mouse.

**In short:** anything the EasyEDA API allows, this plugin can do autonomously upon your request.

### 🛠️ Installation (Antigravity / Claude Desktop ↔ EasyEDA Pro)

- Load the `easyeda_plugin.eext` (or `.zip`) file via the Extension Manager in EasyEDA Pro.
- Add the MCP server configuration to your AI client (e.g. Antigravity or Claude Desktop):

```json
"easyeda_pro": {
  "command": "python",
  "args": [
    "C:/path/to/your/EasyEDA_MCP/easyeda_mcp.py"
  ]
}
```

### 🔌 Connection

- MCP Server Port: `stdio`
- WebSocket Bridge Port: `8787`
- Target URL: `https://pro.easyeda.com/editor`

### 🎮 How to use

1. Start the MCP server via your AI client's configuration.
2. Open EasyEDA Pro in the browser; the plugin will automatically connect via WebSocket.
3. Ask the AI to "Place all components on the PCB" or "Assign 3D models to my resistors".
4. The AI will read the API catalog and execute the magic live in your editor!

**Server output (example):**

```text
[INFO] Starting EasyEDA WebSocket Server on ws://localhost:8787
[INFO] ATM_MCP WebSocket connected
[INFO] ATM_MCP event: execute-js
```

### 📦 Build/Run

- Python 3.10+
- `websockets` library
- Chrome/Edge browser

### ⚠️ Notes

- Ensure EasyEDA Pro is open and the active tab before running complex PCB placement macros.
- Because the AI has access to the full undocumented API, complex macros might require some trial and error depending on the EasyEDA version.

### 🔒 Security Warning

The `execute_js` tool gives the connected AI **unrestricted JavaScript execution** inside your EasyEDA Pro session — this is effectively full remote-control access to whatever project is open, including the ability to read, modify, or delete schematic and PCB data.

- Only run this MCP server when you intend to let an AI act on your CAD session; stop it (or close EasyEDA Pro) otherwise.
- Only connect it to AI clients and prompts you trust — arbitrary code execution against a live design file is not something to expose to untrusted input.
- The WebSocket bridge listens on `127.0.0.1:8787` with no authentication. It is local-only by default, but keep it that way — do not port-forward or expose it on a network interface.
- Consider working on a copy of your project, or keeping frequent backups/version control, before running large automated macros (bulk placement, routing, deletions).

### 🧩 Requirements

- Python 3.10+
- `pip install websockets mcp`
- EasyEDA Pro, running in Chrome or Edge (the plugin bridges the browser tab to the local MCP server)
- An MCP-compatible AI client (Claude Desktop, Antigravity, etc.) configured to launch `easyeda_mcp.py`

### 🩺 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Port 8787 is already in use` on startup | Another instance of the server is already running | Close the other instance, or check for a stale Python process holding the port |
| `Error: EasyEDA is not connected` when calling a tool | The browser plugin hasn't established the WebSocket connection yet | Confirm EasyEDA Pro is open with the plugin active in the current tab, and that the address is `https://pro.easyeda.com/editor` |
| `Timeout waiting for a response from EasyEDA` | The requested operation is slow, or the tab lost focus/was navigated away | Keep the EasyEDA tab active and retry; increase the `timeout` in `send_event` for heavy macros |
| Tool calls silently do nothing | The script inside `execute_js` didn't `return` a value, or used a command that doesn't exist | Call `get_api_catalog` first to confirm the exact command name and syntax |

### 🗺️ Roadmap ideas

- Add authentication/token handling to the WebSocket bridge for safer multi-user or networked setups.
- Cache the API catalog locally to reduce repeated lookups.
- Add a dry-run mode for `execute_js` that reports intended changes without applying them.

---
