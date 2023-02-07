#!/usr/bin/env python3

import pickle
from datetime import date
from os import path

import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)
taskfile = "taskfile"

color_dict = {'b': Fore.LIGHTBLUE_EX, 'bb': Fore.BLUE,
              'm': Fore.LIGHTMAGENTA_EX, 'mm': Fore.MAGENTA,
              'c': Fore.LIGHTCYAN_EX, 'cc': Fore.CYAN,
              'y': Fore.YELLOW, 'yy': Fore.YELLOW,
              'r': Fore.LIGHTRED_EX, 'rr': Fore.LIGHTRED_EX,
              'w': Fore.WHITE}

opcode_dict = {'d': 'done', 'g': 'taken_care_of', 'f': 'irrelevant', 'u': 'urgent', 'h': 'priority'}


def sys_print(text):
    print(f"{Fore.RED}{text}")


def load_data(taskfile):
    if not path.isfile(taskfile):
        State = {"display_done": True, "display_taken_care_of": True, "mark_priority": True, "display_priority": False,
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


def update_tasks(Tasks):
    for task in Tasks:
        task.update_status()


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
                'h to hide/display all highligthed tasks\n' \
                'Example: "d" -> display/dont display done tasks.\n' \
                'add a subtask - type the task number followed by the new task\n' \
                ' # d (to toggle Done/UnDone)\n' \
                ' # e (to toggle sub items expantion display)\n' \
                ' # h (to toggle highlight on a task\n' \
                ' # c (change task color) followed by color to change color - r, g, b, c ,m, y, k, w for cyan, blue...\n' \
                ' # r rename task \n' \
                ' # g to toggle a marker\n' \
                ' # f to toggle red mark and hide\n' \
                ' # p dayofthemonth to set task periodically,\n' \
                ' # w/s to move task up or down (as the number of characters).\n' \
                ' # rm/del to remove task (delete).\n' \
                'Example: "6 2 c m" -> color subtask 2 in task 6 in magenta.\n' \
                '..\n' \
                'Good luck! press enter to continue.\n'
    sys_print(help_text)
    input()


class Task:
    def __init__(self, name, color=color_dict['r']):
        self.name = name
        self.color = color
        self.subTasks = []
        self.expand = True
        self.creation_date = date.today()
        self.done_date = None
        self.status = {'done': False, 'taken_care_of': False, 'irrelevant': False, 'urgent': False, 'priority': False}
        self.period = {'activationDay': 0, 'lastActivation': date.today()}

    def update_status(self):
        today = date.today()
        if self.status['done'] is True and self.status['priority'] is True and self.period['activationDay'] == 0:
            if today.month > self.done_date.month:
                self.status['priority'] = False
                self.status['urgent'] = False

        if self.period['lastActivation'].month != today.month:
            if int(self.period['activationDay']) <= today.day:
                self.period['lastActivation'] = today
                self.set_status('done', False)

        for subTask in self.subTasks:
            subTask.update_status()

    def add_subTask(self, name):
        self.subTasks.append(Task(name, color=self.color))

    def set_color(self, color):
        for subTask in self.subTasks:
            subTask.set_color(color)
        self.color = color

    def set_status(self, key, val):
        self.status[key] = val
        for subTask in self.subTasks:
            subTask.set_status(key, val)

        if key == 'done' and val == True:
            self.done_date = date.today()

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
        if State['display_priority'] is True and self.status['priority'] is False:
            visible = False
        elif self.status['irrelevant'] is True and State['display_irrelevant'] is False:
            visible = False
        elif self.status['done'] is True and State['display_done'] is False:
            visible = False
        elif self.status['taken_care_of'] is True and State['display_taken_care_of'] is False:
            visible = False
        else:
            visible = True

        bg_color = Back.BLACK
        fg_color = self.color
        for key, val in self.status.items():
            if val is True:
                bg_color, fg_color = color_scheme(key)
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
            bg, fg = color_scheme(key)
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
                if State['display_priority'] is True:
                    sub_start = start + str(i) + '.'
                else:
                    sub_start = ''.join([' ' for _ in range(start.count(' '))]) + '    ' + str(i) + '.'
                subTask.print(State, start=sub_start)


class Command:
    def __init__(self, raw_cmd):
        self.cmd, self.next_raw_cmd = self.commad_separator(raw_cmd)
        self.opcode = self.extract_opcode()
        self.task_location = self.extract_task_location()
        self.data = self.extract_data()

    def commad_separator(self, raw_cmd):
        split_cmd = raw_cmd.split(';')
        cmd = split_cmd[0].lstrip().split(' ')
        next_raw_cmd = None if len(split_cmd[1:]) == 0 else ';'.join(split_cmd[1:])

        return cmd, next_raw_cmd

    def extract_opcode(self):
        return next((word for word in self.cmd if not word.isnumeric()), None)

    def extract_task_location(self):
        task_location = list()
        root_task = next((word for word in self.cmd if word.isnumeric()), None)
        if root_task is None:
            return task_location

        root_index = self.cmd.index(root_task)
        task_location.append(int(root_task))
        for word in self.cmd[root_index + 1:]:
            if word.isnumeric():
                task_location.append(int(word))
            else:
                break

        return task_location

    def extract_data(self):
        if self.opcode is not None:
            self.cmd.remove(self.opcode)
        for i in self.task_location:
            self.cmd.remove(str(i))

        return ' '.join(self.cmd)

    def execute(self, State, Tasks):
        if len(self.task_location) == 0:
            execute_command_general(self, State, Tasks)
        else:
            execute_command_specific(self, State, Tasks)

        if self.next_raw_cmd is not None:
            cmd = Command(self.next_raw_cmd)
            cmd.execute(State, Tasks)

        State['prv_src_pointer'] = self.task_location


def display_tasks(State, Tasks):
    if State['display']:
        sys_print('---------------------------------------------------------------------------------------------------')
        for i, task in enumerate(Tasks):
            task.print(State, start=' ' + str(i) + '.')
        sys_print('---------------------------------------------------------------------------------------------------')
    else:
        State['display'] = True


def color_scheme(status_key):
    bg_color = Back.BLACK
    fg_color = ''

    if status_key == 'done':
        fg_color = Fore.LIGHTGREEN_EX

    elif status_key == "taken_care_of":
        fg_color = Fore.GREEN

    elif status_key == "irrelevant":
        fg_color = Fore.RED + Style.DIM

    elif status_key == 'urgent':
        fg_color = Fore.LIGHTYELLOW_EX

    return bg_color, fg_color


def get_task(Tasks, task_pointer_list):
    task = Tasks[task_pointer_list[0]]
    for num in task_pointer_list[1:]:
        task = task.subTasks[num]
    return task

def execute_command_general(cmd, State, Tasks):
    if cmd.opcode == 'help':
        print_instructions(State)

    elif cmd.opcode in opcode_dict:
        property_name = 'display_' + opcode_dict[cmd.opcode]
        State[property_name] = not State[property_name]

        if cmd.opcode == 'h':
            State['expand_all'] = True
            for task in Tasks:
                task.set_expension(State['expand_all'])

    elif cmd.opcode == 'e':
        State['display_priority'] = False
        State['expand_all'] = not State['expand_all']
        for task in Tasks:
            task.set_expension(State['expand_all'])

    elif cmd.opcode == 'v':
        State['verbose'] = not State['verbose']

    elif cmd.opcode == 'c':
        State['display'] = False
        sys_print('arguments for color command are:')
        for key, val in color_dict.items():
            print(f"{val}{key}")

    else:
        new_task = ' '.join([cmd.opcode, cmd.data])
        Tasks.append(Task(new_task))


def execute_command_specific(cmd, State, Tasks):
    task = get_task(Tasks, cmd.task_location)

    if cmd.opcode == None:
        State['display_priority'] = False
        sys_print(task.status)
        sys_print(task.period)
        for Task in Tasks:
            Task.set_expension(False)
        task.set_expension(True)

    elif cmd.opcode in opcode_dict:
        property_name = opcode_dict[cmd.opcode]
        current_val = task.status[property_name]
        task.set_status(property_name, not current_val)

        if cmd.opcode == 'u':
            task.status['priority'] = True if task.status['urgent'] is True else task.status['priority']

    elif cmd.opcode == 'e':
        State['display_priority'] = False
        task.set_expension(not task.expand)

    elif cmd.opcode == 'r':
        task.name = cmd.data

    elif cmd.opcode == 'p':
        task.period = {'activationDay': cmd.data, 'lastActivation': date.today()}

    elif all(chr == 'w' for chr in cmd.opcode) or all(chr == 's' for chr in cmd.opcode):
        direction = 1 if cmd.opcode.startswith('s') else -1
        dst = cmd.task_location[-1] + direction * len(cmd.opcode)
        parent_task_list = Tasks if len(cmd.task_location) == 1 else get_task(Tasks, cmd.task_location[:-1]).subTasks
        parent_task_list.insert(dst, parent_task_list.pop(parent_task_list.index(task)))

    elif cmd.opcode == 'rm' or cmd.opcode == 'del':
        pointer = cmd.task_location[-1]
        if len(cmd.task_location) == 1:
            del Tasks[pointer]
        else:
            parent_task = get_task(Tasks, cmd.task_location[:-1])
            del parent_task.subTasks[pointer]

    elif cmd.opcode == 'c':
        color_code = cmd.data if cmd.data in color_dict.keys() else 'w'
        color = color_dict[color_code]
        task.set_color(color)

    else:
        if not cmd.opcode in opcode_dict:
            task.add_subTask(' '.join([cmd.opcode, cmd.data]))


def main():
    global taskfile
    State, Tasks = load_data(taskfile)
    update_tasks(Tasks)

    sys_print('welcome to TODO list:')
    display_tasks(State, Tasks)

    while True:
        cmd = Command(input())
        cmd.execute(State, Tasks)

        display_tasks(State, Tasks)
        save_data(taskfile, State, Tasks)


if __name__ == '__main__':
    main()
