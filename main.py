#!/usr/bin/env python3

import pickle
from datetime import date
from os import path

import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)
taskfile = "taskfile"

color_dict = {'b': Fore.LIGHTBLUE_EX, 'm': Fore.LIGHTMAGENTA_EX,
              'c': Fore.LIGHTCYAN_EX, 'y': Fore.YELLOW,
              'r': Fore.LIGHTRED_EX, 'w': Fore.WHITE}


def sys_print(text):
    print(f"{Fore.RED}{text}")


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
                ' # p dayofthemonth to set task periodically,\n' \
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
        self.period = {'activationDay': 0, 'lastActivation': date.today()}

    def update_status(self):
        today = date.today()
        if self.status['done'] is True and self.status['priority'] is True and self.period['activationDay'] == 0:
            if today.month > self.done_date.month:
                self.status['priority'] = False

        if self.period['lastActivation'].month != today.month:
            if self.period['activationDay'] >= today.day:
                self.period['lastActivation'] = today
                self.status['done'] = False

        for subTask in self.subTasks:
            subTask.update_status()

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


def display_tasks(State, Tasks):
    if State['display']:
        sys_print('---------------------------------------------------------------------------------------------------')
        for i, task in enumerate(Tasks):
            task.print(State, start=' ' + str(i) + '.')
        sys_print('---------------------------------------------------------------------------------------------------')
    else:
        State['display'] = True


def color_scheme(State, status_key):
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

    elif status_key == 'priority':
        if State["mark_priority"] is True and State['priority_only'] is False:
            fg_color = Fore.LIGHTYELLOW_EX

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


def execute_command_general(cmd, State, Tasks):
    if cmd.opcode == 'help':
        print_instructions(State)

    elif cmd.opcode == 'd':
        State['display_done'] = not State['display_done']

    elif cmd.opcode == 'f':
        State['display_irrelevant'] = not State['display_irrelevant']

    elif cmd.opcode == 'g':
        State['display_taken_care_of'] = not State['display_taken_care_of']

    elif cmd.opcode == 'h':
        State['priority_only'] = not State['priority_only']
        State['expand_all'] = True
        for task in Tasks:
            task.set_expension(State['expand_all'])

    elif cmd.opcode == 'hh':
        State['mark_priority'] = not State['mark_priority']

    elif cmd.opcode == 'e':
        State['priority_only'] = False
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

    elif cmd.opcode == 'w' or cmd.opcode == 's':
        direction = - 1 if cmd.opcode == 'w' else 1
        State['prv_src_pointer'] = swap_tasks(Tasks, State['prv_src_pointer'], direction)

    else:
        new_task = ' '.join([cmd.opcode, cmd.data])
        Tasks.append(Task(new_task))


def execute_command_specific(cmd, State, Tasks):
    task = get_task(Tasks, cmd.task_location)

    if cmd.opcode == 'rm' or cmd.opcode == 'del':
        pointer = cmd.task_location[-1]
        if len(cmd.task_location) == 1:
            del Tasks[pointer]
        else:
            parent_task = get_task(Tasks, cmd.task_location[:-1])
            del parent_task.subTasks[pointer]

    elif cmd.opcode == 'd':
        task.status['done'] = not task.status['done']
        task.status['urgent'] = False
        task.done_date = date.today()

    elif cmd.opcode == 'e':
        State['priority_only'] = False
        task.set_expension(not task.expand)

    elif cmd.opcode == 'ee':
        State['priority_only'] = False
        State['expand_all'] = False
        for ttask in Tasks:
            ttask.set_expension(State['expand_all'])
        task.set_expension(True)

    elif cmd.opcode == 'r':
        task.name = cmd.data

    elif cmd.opcode == 'h':
        task.status['priority'] = not task.status['priority']

    elif cmd.opcode == 'u':
        task.status['urgent'] = not task.status['urgent']
        task.status['priority'] = True if task.status['urgent'] is True else task.status['priority']

    elif cmd.opcode == 'g':
        task.status['taken_care_of'] = not task.status['taken_care_of']
        task.status['urgent'] = False

    elif cmd.opcode == 'f':
        task.status['irrelevant'] = not task.status['irrelevant']

    elif cmd.opcode == 'p':
        task.period = {'activationDay': cmd.data, 'lastActivation': date.today()}

    elif cmd.opcode == 'w' or cmd.opcode == 's':
        direction = - 1 if cmd.opcode == 'w' else 1
        State['prv_src_pointer'] = swap_tasks(Tasks, cmd.task_location, direction)

    elif cmd.opcode == 'ww' or cmd.opcode == 'ss':
        pointer = cmd.task_location[-1]
        if len(cmd.task_location) == 1:
            length = len(Tasks)
        else:
            parent_task = get_task(Tasks, cmd.task_location[:-1])
            length = len(parent_task.subTasks)

        direction = - pointer if cmd.opcode == 'ww' else length - pointer - 1
        State['prv_src_pointer'] = swap_tasks(Tasks, cmd.task_location, direction)

    elif cmd.opcode == 'c':
        color_code = cmd.data[0] if cmd.data[0] in color_dict.keys() else 'w'
        color = color_dict[color_code]
        task.set_color(color)

    elif cmd.opcode == None:
        sys_print(f"{task.status}")
        sys_print(f"{task.period}")

        temp_expension = task.expand

        task.set_expension(True)
        temp = {"display_done": True, "display_taken_care_of": True, "mark_priority": True, "priority_only": False,
                "display_irrelevant": True, 'expand_all': True, 'verbose': True, 'prv_src_pointer': [0]}
        task.print(temp)

        task.set_expension(temp_expension)
        State['display'] = False

    else:
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
