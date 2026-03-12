"""
In-memory background task manager with AJAX polling support.

Replaces the Tkinter BackgroundTask/ConsoleRedirector with a thread-based
approach that buffers output for polling by the browser.
"""

import sys
import threading
import traceback
import uuid
from dataclasses import dataclass, field


@dataclass
class TaskState:
    """Holds the state of a running background task."""
    task_id: str
    status: str = 'running'  # running, completed, error
    output_lines: list = field(default_factory=list)
    result: object = None
    error: str = ''
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _read_index: int = 0

    def append_output(self, text):
        with self._lock:
            self.output_lines.append(text)

    def get_new_output(self):
        with self._lock:
            new = self.output_lines[self._read_index:]
            self._read_index = len(self.output_lines)
            return new

    def get_all_output(self):
        with self._lock:
            return list(self.output_lines)


class TaskOutputWriter:
    """File-like object that captures writes into a TaskState."""

    def __init__(self, task_state):
        self.task_state = task_state

    def write(self, text):
        if text:
            self.task_state.append_output(text)

    def flush(self):
        pass


# Global task registry
_tasks = {}
_tasks_lock = threading.Lock()


def start_task(task_function, success_callback=None, error_callback=None):
    """
    Start a background task, capturing its stdout output.

    Args:
        task_function: Callable to run in background thread.
        success_callback: Called with result on success (in the background thread).
        error_callback: Called with exception on error (in the background thread).

    Returns:
        str: The task ID for polling.
    """
    task_id = str(uuid.uuid4())
    state = TaskState(task_id=task_id)

    with _tasks_lock:
        _tasks[task_id] = state

    def run():
        original_stdout = sys.stdout
        try:
            sys.stdout = TaskOutputWriter(state)
            result = task_function()
            state.result = result
            state.status = 'completed'
            if success_callback:
                success_callback(result)
        except Exception as e:
            state.error = str(e)
            state.append_output(f"\nError: {e}\n")
            state.append_output(traceback.format_exc())
            state.status = 'error'
            if error_callback:
                error_callback(e)
        finally:
            sys.stdout = original_stdout

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return task_id


def get_task(task_id):
    """Get a task state by ID."""
    with _tasks_lock:
        return _tasks.get(task_id)


def cleanup_task(task_id):
    """Remove a completed task from the registry."""
    with _tasks_lock:
        _tasks.pop(task_id, None)
