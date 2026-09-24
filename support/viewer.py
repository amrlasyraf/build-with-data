"""Open DuckDB's local UI with the pipeline database attached read-only."""

from pathlib import Path
import sys

# VS Code's Run button starts this file directly, outside the project package.
if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb

from support.pipeline.settings import DATABASE_PATH, OUTPUT_DIR


def connect_viewer():
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError("Database not found. Run Bronze first.")
    # The UI needs writable storage for its own state, separate from pipeline data.
    connection = duckdb.connect(str(OUTPUT_DIR / "viewer.duckdb"))
    try:
        database_literal = str(DATABASE_PATH).replace("'", "''")
        connection.execute(f"ATTACH '{database_literal}' AS retail (READ_ONLY)")
        return connection
    except Exception:
        connection.close()
        raise


def main() -> int:
    try:
        with connect_viewer() as connection:
            print("Starting DuckDB's local data explorer...", flush=True)
            print("The UI extension and browser assets need internet access.", flush=True)
            connection.execute("INSTALL ui")
            connection.execute("LOAD ui")
            connection.execute("CALL start_ui()")
            print("In the browser, expand retail to inspect the layers you have built.")
            print("Example queries are in the Bronze, Silver, and Gold guides.")
            print("Keep this window open while exploring.")
            print("Close this viewer BEFORE rerunning the pipeline.")
            try:
                input("Press Enter here to stop the viewer: ")
            except (EOFError, KeyboardInterrupt):
                pass
            finally:
                connection.execute("CALL stop_ui_server()")
    except (duckdb.Error, OSError) as error:
        print(f"Could not open the viewer: {error}")
        print("Check your connection if downloading the UI failed.")
        print("For a database lock error, close other viewers or wait for the pipeline to finish.")
        print("For a port conflict, close the other DuckDB UI before trying again.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
