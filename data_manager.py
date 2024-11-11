import pickle

import dropbox

from config import DROPBOX_TOKEN, TASK_FILE_NAME, sys_print

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
        data = [{"display_done": True, "display_taken_care_of": True, "mark_priority": True, "display_priority": False,
                 "display_irrelevant": True, 'expand_all': True, 'verbose': False, 'prv_src_pointer': [0],
                 'display': False,
                 "display_urgent": False, "constant_parent_task": []}, list()]

    State = data[0]
    Tasks = data[1]

    return State, Tasks


def save_data(State, Tasks):
    data = [State, Tasks]
    _upload_file(data, file_path)
