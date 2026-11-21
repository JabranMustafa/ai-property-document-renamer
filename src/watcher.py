from pathlib import Path
import subprocess
import sys
import time
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# ============================================================
# SETTINGS
# ============================================================

PROJECTS_ROOT = Path(
    r"C:\Users\Jabran Mustafa\Desktop\ai assignment appartment\_Task Example AI-Student"
)

MAIN_SCRIPT = Path(__file__).resolve().parent / "main.py"

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png"
}


# Wait a little after the last file event.
# This helps avoid processing a PDF while it is still being copied.
DEBOUNCE_SECONDS = 5


# ============================================================
# WATCHER
# ============================================================

class DocumentWatcher(FileSystemEventHandler):

    def __init__(self):

        self.timer = None
        self.is_running = False
        self.lock = threading.Lock()


    # --------------------------------------------------------
    # CHECK WHETHER EVENT IS RELEVANT
    # --------------------------------------------------------

    def is_relevant(self, path_string, is_directory):

        path = Path(path_string)

        # New folder
        if is_directory:

            # We care about MUC folders
            if "MUC" in path.name.upper():

                return True

            return False


        # New supported document
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:

            return True


        return False


    # --------------------------------------------------------
    # SCHEDULE PROCESSING
    # --------------------------------------------------------

    def schedule_processing(self):

        with self.lock:

            if self.timer:

                self.timer.cancel()


            self.timer = threading.Timer(
                DEBOUNCE_SECONDS,
                self.run_main_program
            )

            self.timer.start()


    # --------------------------------------------------------
    # RUN MAIN PROGRAM
    # --------------------------------------------------------

    def run_main_program(self):

        with self.lock:

            if self.is_running:

                return

            self.is_running = True


        try:

            print("\n" + "=" * 80)

            print(
                "NEW DOCUMENT ACTIVITY DETECTED"
            )

            print(
                "Running document renaming workflow..."
            )

            print("=" * 80)


            subprocess.run(
                [
                    sys.executable,
                    str(MAIN_SCRIPT)
                ],
                check=False
            )


            print("\nWorkflow finished.")

            print(
                "Waiting for new documents..."
            )


        finally:

            with self.lock:

                self.is_running = False


    # --------------------------------------------------------
    # NEW FILE / FOLDER CREATED
    # --------------------------------------------------------

    def on_created(self, event):

        if not self.is_relevant(
            event.src_path,
            event.is_directory
        ):

            return


        print(
            "\nDetected new:",
            event.src_path
        )


        self.schedule_processing()


    # --------------------------------------------------------
    # FILE / FOLDER MOVED INTO WATCHED AREA
    # --------------------------------------------------------

    def on_moved(self, event):

        if not self.is_relevant(
            event.dest_path,
            event.is_directory
        ):

            return


        print(
            "\nDetected moved item:",
            event.dest_path
        )


        self.schedule_processing()


# ============================================================
# START WATCHER
# ============================================================

if __name__ == "__main__":

    if not PROJECTS_ROOT.exists():

        print(
            "ERROR: Folder does not exist:"
        )

        print(
            PROJECTS_ROOT
        )

        sys.exit(1)


    event_handler = DocumentWatcher()

    observer = Observer()

    observer.schedule(
        event_handler,
        str(PROJECTS_ROOT),
        recursive=True
    )

    observer.start()


    print("=" * 80)

    print(
        "PROPERTY DOCUMENT WATCHER STARTED"
    )

    print(
        "Watching:"
    )

    print(
        PROJECTS_ROOT
    )

    print()

    print(
        "The workflow will automatically run when:"
    )

    print(
        "- a new MUC folder is added"
    )

    print(
        "- a new PDF is added"
    )

    print(
        "- a new JPG / JPEG / PNG is added"
    )

    print()

    print(
        "Waiting for new documents..."
    )

    print(
        "Press Ctrl+C to stop."
    )

    print("=" * 80)


    try:

        while True:

            time.sleep(1)


    except KeyboardInterrupt:

        print(
            "\nStopping watcher..."
        )

        observer.stop()


    observer.join()

    print(
        "Watcher stopped."
    )