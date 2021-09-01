import os
from threading import Lock

mutex = Lock()


def read_progress(job_id):
    mutex.acquire()
    try:
        progress_file_path = os.path.join(job_id, 'progress.txt')
        if os.path.exists(progress_file_path) is False:
            return "Invalid Job ID"
        with open(progress_file_path, "r") as f:
            percent = f.read()
        return percent
    finally:
        mutex.release()


def write_progress(job_id, percent):
    mutex.acquire()
    try:
        progress_file_path = os.path.join(job_id, 'progress.txt')
        with open(progress_file_path, "w") as f:
            f.write(percent)
    finally:
        mutex.release()
