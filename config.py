import yaml

with open('credentials.yml', 'r') as file:
    credentials = yaml.load(file, Loader=yaml.FullLoader)

DROPBOX_TOKEN = credentials['dropbox_token']
TASK_FILE_NAME = "todo_list_task_file"

_version_major = 1
_version_minor = 1
_version_build = 1
VERSION = f"{_version_major}_{_version_minor}_{_version_build}"

MAX_UNSAVED_TIME = 180
MAX_UNSAVED_COMMANDS = 10

STRIKE_THROUGH_CODE = '\033[9m'
UNDERLINE_CODE = '\033[4m'
RESET_ALL_CODE = '\x1b[0m'


def ansi_256_color(color_code):
    return f'\033[38;5;{color_code}m'


def sys_print(text):
    print(f"{ansi_256_color(225)}{text}{RESET_ALL_CODE}")


FG_COLOR_DONE = STRIKE_THROUGH_CODE + ansi_256_color(77)
FG_COLOR_TAKEN_CARE_OF = ansi_256_color(71)
FG_COLOR_DONE_IRRELEVANT = STRIKE_THROUGH_CODE + ansi_256_color(167)
CROSS_SECTION_LINE = '-------------------------------------------------------------------------------------------------'

initial_state = {"display_done": True,
                 "display_taken_care_of": True,
                 "mark_priority": True,
                 "display_priority": False,
                 "display_irrelevant": True,
                 'expand_all': True,
                 'verbose': False,
                 'prv_src_pointer': [0],
                 'display': False,
                 "display_urgent": False,
                 "constant_parent_task": []}

color_dict = {'b': ansi_256_color(27), 'bb': ansi_256_color(33), 'bbb': ansi_256_color(75),
              'c': ansi_256_color(51), 'cc': ansi_256_color(45),
              'g': ansi_256_color(46), 'gg': ansi_256_color(40),
              'm': ansi_256_color(93), 'mm': ansi_256_color(129),
              'p': ansi_256_color(201), 'pp': ansi_256_color(207),
              'y': ansi_256_color(11), 'yy': ansi_256_color(184),
              'o': ansi_256_color(214), 'oo': ansi_256_color(208), 'ooo': ansi_256_color(202),
              'br': ansi_256_color(130), 'brbr': ansi_256_color(124),
              'r': ansi_256_color(196), 'rr': ansi_256_color(160),
              'w': ansi_256_color(15), 'ww': ansi_256_color(255),
              'gr': ansi_256_color(244), 'grgr': ansi_256_color(246)}

opcode_dict = {'d': 'done',
               'g': 'taken_care_of',
               'f': 'irrelevant',
               'u': 'urgent',
               'h': 'priority'}

HELP_TEXT = """Welcome to TODO list.

    GENERAL COMMANDS:
    - help: Display this menu.
    - <task name>: Create a new task.
    - e: Expand/collapse all tasks.
    - d: Toggle display of done tasks.
    - f: Toggle display of irrelevant tasks.
    - g: Toggle display of taken care of tasks.
    - v: Toggle display of date log.
    - h: Display only high-importance tasks.
    - u: Display only urgent tasks.

    SPECIFIC COMMANDS (for task #):
    - To add a subtask: Type the task number followed by the new subtask.
    - #: Expand only this task and see its status.
    - # rm/del: Remove task (delete).
    - # d: Toggle Done/UnDone for the task.
    - # dd: Toggle Done/UnDone for all subtasks.
    - # w/s: Move task up or down.
    - # e: Toggle display of sub items expansion.
    - # h: Toggle high-importance state.
    - # u: Toggle urgent state.
    - # r: Rename task followed by the new task name.
    - # g: Toggle taken care of state.
    - # f: Toggle irrelevant state.
    - # p dayofthemonth: Set task periodically.
    - # c color: Change task color (r, g, b, c, m, y, k, w for cyan, blue...).

    Example: "6 2 c m" - Color subtask 2 of task 6 in magenta.
    """
