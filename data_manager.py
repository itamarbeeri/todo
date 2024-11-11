import pickle

import dropbox

from config import VERSION, DROPBOX_TOKEN, TASK_FILE_NAME, initial_state, sys_print

dbx = dropbox.Dropbox(DROPBOX_TOKEN)
file_path = f'/{TASK_FILE_NAME}'


def _upload_file(content, file_path):
    pickled_content = pickle.dumps(content)
    dbx.files_upload(pickled_content, file_path, mode=dropbox.files.WriteMode("overwrite"))


def _download_file(file_path):
    metadata, res = dbx.files_download(file_path)
    pickled_content = res.content
    return pickle.loads(pickled_content)


def load_data():
    try:
        data = _download_file(file_path)
    except:
        sys_print('creating a new task file..')
        data = [VERSION, list()]

    Version = data[0]
    Tasks = data[1]
    State = initial_state

    if Version != VERSION:
        sys_print(f"MISS MATCHED VERSIONS! \n app version: {VERSION}, data version: {Version}")

    return State, Tasks


def save_data(State, Tasks):
    data = [VERSION, Tasks]
    _upload_file(data, file_path)
    sys_print('--data saved--')

