from config import TASK_FILE_NAME, sys_print
import pickle
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Opens a web browser to authenticate
drive = GoogleDrive(gauth)

def _upload_file(content, file_id=None):
    pickled_content = pickle.dumps(content)
    file = drive.CreateFile({'id': file_id}) if file_id else drive.CreateFile({'title': TASK_FILE_NAME})
    file.SetContentString(pickled_content.decode('latin-1'))
    file.Upload()
    return file['id']

def _find_file_ID():
    file_list = drive.ListFile({'q': f"title = '{TASK_FILE_NAME}' and trashed = false"}).GetList()

    if file_list:
        sys_print('task file detected on drive')
        return file_list[0]['id']
    else:
        sys_print('task file NOT detected on drive')
        return None

def _download_file(file_id):
    file = drive.CreateFile({'id': file_id})
    content = file.GetContentString()
    content_bytes = content.encode('latin-1')  # Convert the string back to bytes
    return pickle.loads(content_bytes)

def load_data(file_ID=None):
    file_ID = file_ID if file_ID else _find_file_ID()
    if not file_ID:
        sys_print('creating a new task file..')
        State = {"display_done": True, "display_taken_care_of": True, "mark_priority": True, "display_priority": False,
                 "display_irrelevant": True, 'expand_all': True, 'verbose': False, 'prv_src_pointer': [0], 'display': False,
                 "display_urgent": False, "constant_parent_task": []}
        return State, []

    data = _download_file(file_ID)
    State = data[0]
    Tasks = data[1]

    return file_ID, State, Tasks

def save_data(file_ID, State, Tasks):
    data = [State, Tasks]
    file_ID = _upload_file(data, file_ID)
    return file_ID