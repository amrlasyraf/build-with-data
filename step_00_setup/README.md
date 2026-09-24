# 00 — Set up your computer

This is a hands-on project. Nothing runs just because you download it. You
will create a Python environment, install the packages, and run Bronze, Silver,
and Gold yourself from a terminal.

## What you need

| Tool | Required? | Why |
|---|---|---|
| [Python 3.11 or newer](https://www.python.org/downloads/) | Yes | Runs the pipeline and creates its virtual environment |
| PowerShell on Windows | Yes for these copy-and-paste commands | Runs the commands below |
| Internet connection on first setup | Yes | Downloads Python packages |
| [VS Code](https://code.visualstudio.com/Download) | Recommended | Makes it easier to browse the folders, edit code, and open a terminal |
| [Python extension for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-python.python) | Recommended with VS Code | Adds Python editing and interpreter support; it does not install Python |
| Git | No | You can use GitHub's **Download ZIP** instead |
| Power BI Desktop | No | Needed only for the optional report in Step 05 |

The `requirements.txt` file in this folder lists the project's Python packages.
DuckDB is installed by the package command below; you do not need to install
a DuckDB server.

## Prepare the project

1. Download the project from GitHub with **Code → Download ZIP**, then extract
   it. Do not work from inside the ZIP.
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

`_local/` is ignored by Git. Your environment and generated database stay on
your computer; they are not included in the repository.

Next: [01 — Source data](../step_01_data/README.md). After looking at the CSVs,
run Bronze using the command in [Step 02](../step_02_bronze/README.md).
