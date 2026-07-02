import os
import pickle

from config import VERSION, TASK_FILE_NAME, initial_state, sys_print

file_path = TASK_FILE_NAME


def save_data(State, Tasks):
    with open(file_path, 'wb') as f:
        pickle.dump([VERSION, Tasks], f)
    sys_print('--data saved--')


def load_data():
    if not os.path.exists(file_path):
        sys_print('creating a new task file..')
        return initial_state, list()

    with open(file_path, 'rb') as f:
        data = pickle.load(f)

    version = data[0]
    Tasks = data[1]
    State = initial_state

    if version != VERSION:
        sys_print(f"MISS MATCHED VERSIONS! \n app version: {VERSION}, data version: {version}")

    return State, Tasks
