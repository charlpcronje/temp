# ✅ Add Interactive Mode to Existing CLI + API Python App

---

You're an expert Python developer and TUI designer. I have a completed Python application that exposes both a CLI (Typer) and a REST API (FastAPI), with all business logic organized cleanly into modular `core/` files and a shared `commands.py` registry.

Each command is defined centrally, with:
- `func`: the function to call
- `args`: the arguments it expects
- `description`: human-readable label

Now I want to add a third interface to this system: a **fully interactive Textual-based TUI (terminal user interface)** that visually organizes the system into panels and lets users execute commands using a beautiful navigable layout.

---

### ✳️ Goals for This Interactive Mode

- Built using the **[Textual](https://github.com/Textualize/textual)** framework
- A clean, stylized full-screen terminal interface
- Load command definitions dynamically from `commands.py`
- Allow user interaction without typing commands manually
- Display logs, input prompts, results, and real-time feedback

---

### 🖥️ Layout Requirements

The interface should look like this in terminal:

```
+------------------------+------------------------------+
|        Commands        |         Details Panel        |
|                        |  Shows info about selected   |
|  - Import File         |  command, arguments needed,  |
|  - Validate            |  and current session hash    |
|  - Generate Mapping    |                              |
|  - Generate HTML       |                              |
|  - Generate PDF        |                              |
+------------------------+------------------------------+
|                 Live Logs / Output Panel              |
|   Stream log events, status updates, and results      |
+-------------------------------------------------------+
```

---

### 🧠 Behavior Requirements

- **Left panel**:
  - Lists all commands dynamically from `commands.py`
  - Arrow keys or mouse to select
  - Enter key to run a command
- **Right panel**:
  - Displays selected command’s `description` and expected `args`
  - Prompts user for argument values if required
  - After input, calls the corresponding function
- **Bottom panel**:
  - Live output/logs (captured via a shared logger or event stream)
  - Should stream status like “Importing… Done”, errors, etc.
- **State Awareness**:
  - Reads `status.json` to display session hash and relevant config
  - Displays current session folder name (hash), environment, etc.

---

### 🧩 Technical Notes

- Load all command definitions from `commands.py`
- Use `Textual.widgets` for panels (e.g., `ListView`, `Markdown`, `DataTable`)
- Logs should be redirected to a stream or buffer viewable in the bottom panel
- Prompt for arguments using modal popups or input forms
- Should be fully keyboard-navigable

---

### ✅ Deliverables

Please generate:
1. A new file `tui.py` that launches the Textual app
2. A `TUIApplication` class that:
   - Initializes layout
   - Loads commands
   - Handles input and output
   - Displays real-time logs
3. Use placeholder logic for command execution (can call real core functions if known, else stub them)

Please ensure the app runs from `python tui.py`.