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

---
