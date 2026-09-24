# 00 — Set up your computer

This step covers the local Python setup. The setup commands below use a
terminal once. After that, open each layer's Python file in VS Code and click
**Run Python File**. You do not need to type a command to run a layer.

If a README opens in VS Code showing Markdown symbols such as `#` and `|`,
press **Ctrl+Shift+V** to see the formatted preview. You can also right-click
the file's tab and choose **Open Preview**. On GitHub, README files already
appear formatted.

## What you need

| Tool | Required? | Why |
|---|---|---|
| [Python 3.11 or newer](https://www.python.org/downloads/) | Yes | Runs the pipeline and creates its virtual environment |
| PowerShell on Windows | Yes for these copy-and-paste commands | Runs the commands below |
| Internet connection on first setup | Yes | Downloads Python packages |
| [VS Code](https://code.visualstudio.com/Download) | Yes for the click-to-run path | Opens and runs each layer's Python file |
| [Python extension for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-python.python) | Yes with VS Code | Adds the Run Python File button; it does not install Python |
| Git | No | You can use GitHub's **Download ZIP** instead |
| Power BI Desktop | No | Needed only for the optional report in Step 05 |

The `requirements.txt` file in this folder lists the project's Python packages.
DuckDB is installed by the package command below; you do not need to install
a DuckDB server.

## Prepare the project

1. Download the project from GitHub with **Code → Download ZIP**, then extract
   it. Use the extracted folder for the steps below.
2. Open the extracted repository folder in VS Code, or open PowerShell in that
   folder. The terminal should show the folder containing `README.md`.
3. Check that Python is available:

```powershell
python --version
```

If `python` is not recognized, try `py -3 --version`. If that works, use
`py -3` instead of `python` in the next command. If neither works, install
Python, reopen the terminal, and check again. Confirm the version is 3.11 or
newer before continuing.

4. Create a project-only environment:

```powershell
python -m venv _local\.venv
```

5. Install the packages into that environment:

```powershell
.\_local\.venv\Scripts\python.exe -m pip install -r step_00_setup\requirements.txt
```

6. Confirm the packages can be imported:

```powershell
.\_local\.venv\Scripts\python.exe -c "import pandas, duckdb; print('Ready')"
```

7. In VS Code, press **Ctrl+Shift+P**, choose **Python: Select Interpreter**,
   and select `_local\.venv\Scripts\python.exe`. If it is not listed, choose
   **Enter interpreter path** and browse to that file in the project folder.
   Check that VS Code shows this environment as the selected Python version.

To run a layer later, open its `.py` file and click **Run Python File** (the
play button at the top right of the editor). VS Code displays the program's
output in its terminal panel; you do not need to type a command there.

`_local/` is ignored by Git. Your environment and generated database stay on
your computer; they are not included in the repository.

Next: [01 — Source data](../step_01_data/README.md). After looking at the CSVs,
open `step_02_bronze/bronze.py` and follow [Step 02](../step_02_bronze/README.md).
