from rich.progress import Progress
import time

def sleep_with_progress(duration: int, task_name:str):
    """
    Sleep for a given duration while displaying a loading bar using rich.
    
    :param duration: Total sleep time in seconds.
    """
    with Progress() as progress:
        task = progress.add_task(f"[cyan]{task_name}: Waiting for {duration}s", total=100)
        interval = 0.1  # Update interval in seconds
        total_intervals = int(duration / interval)

        for _ in range(total_intervals):
            time.sleep(interval)
            progress.advance(task, 100 / total_intervals)  # Progress increment