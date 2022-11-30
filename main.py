#!/usr/bin/env python3

import pickle
from datetime import date
from os import path

import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)


def sys_print(text):
    print(f"{Fore.LIGHTRED_EX}{text}")


def print_instructions(State):
    help_text = f'Welcome to TODO list.\n' \
                f'State is: {State}\n' \
                f'..\n' \
                f'To create a new task - type the task name.\n' \
                f'e to expand/collapse all\n' \
                'd to hide/display all done tasks\n' \
                'f to hide/display all irrelevant tasks\n' \
                'g to hide/display all taken_care_of tasks\n' \
                'v to hide/display date log\n' \
                'h to mark/unmark all highligthed tasks\n' \
                'hh to hide/display all highligthed tasks\n' \
                'Example: "d" -> display/dont display done tasks.\n' \
                '\nadd a subtask - type the task number followed by the new task\n' \
                ' # d (to toggle Done/UnDone)\n' \
                ' # e (to toggle sub items expantion display)\n' \
                ' # ee collapse all but this\n' \
                ' # h (to toggle highlight on a task\n' \
                ' # c (change task color) followed by color to change color - r, g, b, c ,m, y, k, w for cyan, blue...\n' \
                ' # r rename task \n' \
                ' # g to toggle a marker\n' \
                ' # f to toggle red mark and hide\n' \
                ' # w/s to move task up or down.\n' \
                ' # ww/ss to move task all the way up or down.\n' \
                ' # rm/del to remove task (delete).\n' \
                'Example: "6 2 c m" -> color subtask 2 in task 6 in magenta.\n' \
                '..\n' \
                'Good luck! press enter to continue.\n'
    sys_print(help_text)
    input()


class Task:
    def __init__(self, name, color=Fore.WHITE):
        self.name = name
        self.color = color
        self.subTasks = []
        self.expand = True
        self.creation_date = date.today()
        self.done_date = None
        self.status = {'done': False, 'taken_care_of': False, 'irrelevant': False, 'urgent': False, 'priority': False}


    def add_subTask(self, name):
        self.subTasks.append(Task(name, color=self.color))

    def set_color(self, color):
        for subTask in self.subTasks:
            subTask.set_color(color)
        self.color = color

    def set_expension(self, val):
        self.expand = val
        for subTask in self.subTasks:
            subTask.set_expension(val)

    def count_status(self):
        counter = {'regular': 0, 'done': 0, 'taken_care_of': 0, 'priority': 0, 'urgent': 0, 'irrelevant': 0}
        for subTask in self.subTasks:
            is_regular = True
            for key, val in subTask.status.items():
                counter[key] += val
                is_regular = False if val is True else is_regular
            counter['regular'] += is_regular
        return counter

    def get_display_params(self, State):
        if State['priority_only'] is True and self.status['priority'] is False:
            visible = False
        elif self.status['done'] is True and State['display_done'] is False:
            visible = False
        elif self.status['taken_care_of'] is True and State['display_taken_care_of'] is False:
            visible = False
        elif self.status['irrelevant'] is True and State['display_irrelevant'] is False:
            visible = False
        else:
            visible = True

        bg_color = Back.BLACK
        fg_color = self.color
        for key, val in self.status.items():
            if val is True:
                bg_color, fg_color = color_scheme(State, key)
                break
        fg_color = self.color if fg_color == '' else fg_color

        return fg_color, bg_color, visible

    def build_appendix(self, State, msg_length=50):
        status = self.count_status()

        task_status = '' if len(self.subTasks) == 0 else f'({status["done"]}/{len(self.subTasks)})'
        expand_sign = '' if len(self.subTasks) == 0 else " ..." if self.expand is False else ':'
        dates = str(self.creation_date) + '-' + str(self.done_date)

        end = task_status + expand_sign
        msg_length += len(end)

        expanded_task_status = '('
        for key, val in status.items():
            bg, fg = color_scheme(State, key)
            expanded_task_status += bg + fg + str(val) + ','
        expanded_task_status[:-1]
        expanded_task_status += Style.RESET_ALL + f' /{len(self.subTasks)})'
        offset = '{:>' + str(max([165 - msg_length, msg_length + 1])) + '}'
        verbose = offset.format(f'{dates}, {expanded_task_status}') if State['verbose'] else ''

        appendix = end + verbose
        return appendix

    def print(self, State, start=None):
        fg_color, bg_color, visible = self.get_display_params(State)

        if visible is True:
            start = '' if start is None else str(start)
            msg = f'{start} {self.name}'
            end = self.build_appendix(State, len(msg))
            print(f"{bg_color}{fg_color}{msg} {end}")

        if self.expand is True:
            for i, subTask in enumerate(self.subTasks):
                if State['priority_only'] is True:
                    sub_start = start + str(i) + '.'
                else:
                    sub_start = ''.join([' ' for _ in range(start.count(' '))]) + '    ' + str(i) + '.'
                subTask.print(State, start=sub_start)


def display_tasks(State, Tasks):
    sys_print('---------------------------------------------------------------------------------------------------------')
    for i, task in enumerate(Tasks):
        task.print(State, start=' ' + str(i) + '.')
    sys_print('---------------------------------------------------------------------------------------------------------')

def color_scheme(State, status_key):
    if status_key == 'done':
        bg_color = Back.BLACK
        fg_color = Fore.GREEN + Style.BRIGHT

    elif status_key == "taken_care_of":
        bg_color = Back.BLACK
        fg_color = Fore.GREEN + Style.DIM

    elif status_key == "irrelevant":
        bg_color = Back.BLACK
        fg_color = Fore.LIGHTRED_EX + Style.DIM

    elif status_key == 'urgent':
        if State['priority_only'] or State["mark_priority"]:
            bg_color = Back.BLACK
            fg_color = Fore.LIGHTYELLOW_EX
        else:
            bg_color = Back.BLACK
            fg_color = ''

    elif status_key == 'priority':
        if State["mark_priority"] is True and State['priority_only'] is False:
            bg_color = Back.BLACK
            fg_color = Fore.YELLOW
        else:
            bg_color = Back.BLACK
            fg_color = ''

    else:
        bg_color = Back.BLACK
        fg_color = ''

    return bg_color, fg_color

def get_task(Tasks, task_pointer_list):
    task = Tasks[task_pointer_list[0]]
    for num in task_pointer_list[1:]:
        task = task.subTasks[num]
    return task


def swap_tasks(Tasks, task_pointer_list, direction):
    pointer = task_pointer_list[-1]
    if len(task_pointer_list) == 1:
        if 0 <= pointer + direction < len(Tasks):
            temp = Tasks[pointer]
            Tasks[pointer] = Tasks[pointer + direction]
            Tasks[pointer + direction] = temp
            task_pointer_list[-1] = pointer + direction
    else:
        parent_task = get_task(Tasks, task_pointer_list[:-1])
        if 0 <= pointer + direction < len(parent_task.subTasks):
            temp = parent_task.subTasks[pointer]
            parent_task.subTasks[pointer] = parent_task.subTasks[pointer + direction]
            parent_task.subTasks[pointer + direction] = temp
            task_pointer_list[-1] = pointer + direction
    return task_pointer_list


def load_data(taskfile):
    if not path.isfile(taskfile):
        State = {"display_done": True, "display_taken_care_of": True, "mark_priority": True, "priority_only": False,
                 "display_irrelevant": True, 'expand_all': True, 'verbose': False, 'prv_src_pointer': [0]}
        return [State, []]

    with open(taskfile, "rb") as fp:
        data = pickle.load(fp)
        State = data[0]
        Tasks = data[1]

    return State, Tasks


def save_data(taskfile, State, Tasks):
    data = [State, Tasks]
    with open(taskfile, "wb") as fp:
        pickle.dump(data, fp)


def parse_command(raw_cmd):
    split_cmd = raw_cmd.split(';')
    next_cmd = None if len(split_cmd) == 1 else ';'.join(split_cmd[1:])

    cmd = split_cmd[0].lower().lstrip()
    cmd_list = cmd.split(' ')
    opcode = next((word for word in cmd_list if not word.isnumeric()), '')
    if opcode != '':
        cmd_list.remove(opcode)

    src_pointer = []
    cmd_offset = 0
    if len(cmd_list) == 0:
        data = ''
    else:
        while cmd_offset < len(cmd_list) and cmd_list[cmd_offset].isnumeric():
            src_pointer.append(int(cmd_list[cmd_offset]))
            cmd_offset += 1
        data = ' '.join(cmd_list[cmd_offset:])
    src_pointer = '' if len(src_pointer) == 0 else src_pointer
    cmd_dict = {'opcode': opcode, 'src_pointer': src_pointer, 'data': data}

    return cmd_dict, next_cmd


def execute_command_general(cmd_dict, State, Tasks):
    if cmd_dict['opcode'] == 'help':
        print_instructions(State)

    elif cmd_dict['opcode'] == 'd':
        State['display_done'] = not State['display_done']

    elif cmd_dict['opcode'] == 'f':
        State['display_irrelevant'] = not State['display_irrelevant']

    elif cmd_dict['opcode'] == 'g':
        State['display_taken_care_of'] = not State['display_taken_care_of']

    elif cmd_dict['opcode'] == 'h':
        State['priority_only'] = not State['priority_only']
        State['expand_all'] = True
        for task in Tasks:
            task.set_expension(State['expand_all'])

    elif cmd_dict['opcode'] == 'hh':
        State['mark_priority'] = not State['mark_priority']

    elif cmd_dict['opcode'] == 'e':
        State['priority_only'] = False
        State['expand_all'] = not State['expand_all']
        for task in Tasks:
            task.set_expension(State['expand_all'])

    elif cmd_dict['opcode'] == 'v':
        State['verbose'] = not State['verbose']

    elif cmd_dict['opcode'] == 'w' or cmd_dict['opcode'] == 's':
        direction = - 1 if cmd_dict['opcode'] == 'w' else 1
        State['prv_src_pointer'] = swap_tasks(Tasks, State['prv_src_pointer'], direction)

    else:
        new_task = ' '.join([cmd_dict['opcode'], cmd_dict['src_pointer'], cmd_dict['data']])
        Tasks.append(Task(new_task))


def execute_command_specific(cmd_dict, State, Tasks):
    task = get_task(Tasks, cmd_dict['src_pointer'])

    if cmd_dict['opcode'] == 'rm' or cmd_dict['opcode'] == 'del':
        pointer = cmd_dict['src_pointer'][-1]
        if len(cmd_dict['src_pointer']) == 1:
            del Tasks[pointer]
        else:
            parent_task = get_task(Tasks, cmd_dict['src_pointer'][:-1])
            del parent_task.subTasks[pointer]

    elif cmd_dict['opcode'] == 'd':
        task.status['done'] = not task.status['done']
        task.status['urgent'] = False
        task.done_date = date.today()

    elif cmd_dict['opcode'] == 'e':
        State['priority_only'] = False
        task.set_expension(not task.expand)

    elif cmd_dict['opcode'] == 'ee':
        State['priority_only'] = False
        State['expand_all'] = False
        for ttask in Tasks:
            ttask.set_expension(State['expand_all'])
        task.set_expension(True)

    elif cmd_dict['opcode'] == 'r':
        task.name = cmd_dict['data']

    elif cmd_dict['opcode'] == 'h':
        task.status['priority'] = not task.status['priority']

    elif cmd_dict['opcode'] == 'u':
        task.status['urgent'] = not task.status['urgent']
        task.status['priority'] = True if task.status['urgent'] is True else task.status['priority']

    elif cmd_dict['opcode'] == 'g':
        task.status['taken_care_of'] = not task.status['taken_care_of']
        task.status['urgent'] = False

    elif cmd_dict['opcode'] == 'f':
        task.status['irrelevant'] = not task.status['irrelevant']

    elif cmd_dict['opcode'] == 'w' or cmd_dict['opcode'] == 's':
        direction = - 1 if cmd_dict['opcode'] == 'w' else 1
        State['prv_src_pointer'] = swap_tasks(Tasks, cmd_dict['src_pointer'], direction)

    elif cmd_dict['opcode'] == 'ww' or cmd_dict['opcode'] == 'ss':
        pointer = cmd_dict['src_pointer'][-1]
        if len(cmd_dict['src_pointer']) == 1:
            length = len(Tasks)
        else:
            parent_task = get_task(Tasks, cmd_dict['src_pointer'][:-1])
            length = len(parent_task.subTasks)

        direction = - pointer if cmd_dict['opcode'] == 'ww' else length - pointer - 1
        State['prv_src_pointer'] = swap_tasks(Tasks, cmd_dict['src_pointer'], direction)

    elif cmd_dict['opcode'] == 'c':
        if cmd_dict['data'].startswith('b'):
            color = Fore.BLUE
        elif cmd_dict['data'].startswith('m'):
            color = Fore.LIGHTMAGENTA_EX
        elif cmd_dict['data'].startswith('c'):
            color = Fore.CYAN
        elif cmd_dict['data'].startswith('w'):
            color = Fore.WHITE
        elif cmd_dict['data'].startswith('k'):
            color = Fore.BLACK
        else:
            color = Fore.WHITE

        task.set_color(color)

    elif cmd_dict['opcode'].lstrip() == '':
        sys_print(f"{task.status}")
        temp_expension = task.expand

        task.set_expension(True)
        temp_state = {"display_done": True, "display_taken_care_of": True, "mark_priority": True, "priority_only": False,
         "display_irrelevant": True, 'expand_all': True, 'verbose': True, 'prv_src_pointer': [0]}
        task.print(temp_state)

        task.set_expension(temp_expension)
        State['display'] = False

    else:
        task.add_subTask(' '.join([cmd_dict['opcode'], cmd_dict['data']]))


def execute_command(State, Tasks, cmd_dict):
    if len(cmd_dict['src_pointer']) == 0:
        execute_command_general(cmd_dict, State, Tasks)
    else:
        execute_command_specific(cmd_dict, State, Tasks)

def main():
    taskfile = "taskfile"
    State, Tasks = load_data(taskfile)
    State['prv_src_pointer'] = [0]
    sys_print('welcome to TODO list:')
    display_tasks(State, Tasks)

    while True:
        cmd = input()
        cmd_dict, next_cmd = parse_command(cmd)
        execute_command(State, Tasks, cmd_dict)

        while next_cmd is not None:
            cmd_dict, next_cmd = parse_command(next_cmd)
            execute_command(State, Tasks, cmd_dict)

        if State['display']:
            display_tasks(State, Tasks)
        else:
            State['display'] = True
        save_data(taskfile, State, Tasks)


if __name__ == '__main__':
    main()
