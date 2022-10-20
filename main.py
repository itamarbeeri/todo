#!/usr/bin/env python3

import pickle
from os import path

import colorama
from colorama import Fore, Back, Style
from datetime import date

colorama.init(autoreset=True)

indent = '    '


def sprint(text):
    print(f"{Fore.LIGHTRED_EX}{text}")


def print_instructions(State):
    sprint('Welcome to TODO list.')
    sprint('Display state is:')
    sprint(State)
    sprint('..')
    sprint('To create a new task - type the task name.')
    sprint('e to expand/collapse all')
    sprint('d to hide/display all done tasks')
    sprint('f to hide/display all irrelevant tasks')
    sprint('g to hide/display all taken_care_of tasks')
    sprint('h to hide/display all highligthed tasks')
    sprint('hh to mark/unmark all highligthed tasks')
    sprint("Example: 'd' -> display/dont display done tasks.")
    sprint('')
    sprint('Edit a task - type the task number followed by command')
    sprint(' # d (to toggle Done/UnDone)')
    sprint(' # e (to toggle sub items expantion display)')
    sprint(' # h (to toggle highlight on a task')
    sprint(' # c (change task color) followed by color to change color - r, g, b, c ,m, y, k, w for cyan, blue...')
    sprint(' # a (add sub task) followed by sub task name')
    sprint(' # g to toggle a marker')
    sprint(' # f to toggle red mark and hide')
    sprint(' # w/s to move task up or down.')
    sprint(' # del to delete task.')
    sprint("Example: '6 2 c m' -> color subtask 2 in task 6 in magenta.")
    sprint('..')
    sprint('Good luck! press enter to continue.')
    input()


class Task:
    def __init__(self, name, color=Fore.WHITE, expendItems=True):
        self.name = name
        self.status = {'done': False, 'taken_care_of': False, 'priority': False, 'irrelevant': False}
        self.itemList = []
        self.color = color
        self.expendItems = expendItems
        self.creation_date = date.today()
        self.done_date = None


    def add_item(self, name):
        self.itemList.append(Task(name, color=self.color))

    def set_color(self, color):
        for item in self.itemList:
            if self.color == item.color:
                item.color = color
        self.color = color

    def done_tasks(self):
        done_counter = 0
        for item in self.itemList:
            if item.status['done'] is True:
                done_counter += 1
        return done_counter

    def set_expension(self, val):
        self.expendItems = val
        for item in self.itemList:
            item.set_expension(val)

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

        if self.status["done"] is True:
            bg_color = Back.BLACK
            fg_color = Fore.GREEN + Style.BRIGHT

        elif self.status["taken_care_of"] is True:
            bg_color = Back.BLACK
            fg_color = Fore.GREEN + Style.DIM

        elif self.status["irrelevant"] is True:
            bg_color = Back.BLACK
            fg_color = Fore.LIGHTRED_EX + Style.BRIGHT

        elif self.status["priority"] is True:
            if State["mark_priority"] is True and State['priority_only'] is False:
                bg_color = Back.BLACK
                fg_color = Fore.YELLOW
            else:
                bg_color = Back.BLACK
                fg_color = self.color + Style.BRIGHT

        else:
            bg_color = Back.BLACK
            fg_color = self.color + Style.BRIGHT

        return fg_color, bg_color, visible

    def print(self, State, start=None):
        global indent
        fg_color, bg_color, visible = self.get_display_params(State)
        done_tasks = '(' + str(self.done_tasks()) + '/' + str(len(self.itemList)) + ')' if len(self.itemList) > 0 else ''
        dates = indent * 3 + str(self.creation_date) + '-' + str(self.done_date) if State['verbose'] or self.status['done'] else ''

        if visible is True:
            start = '' if start is None else str(start)
            end = f'{done_tasks} {dates}' if len(self.itemList) == 0 else f'{done_tasks} {dates} ...'
            print(f"{bg_color}{fg_color}{start} {self.name} {end}")

        if self.expendItems is True:
            for i, item in enumerate(self.itemList):
                if State['priority_only'] is True:
                    sub_start = start + str(i) + '.'
                else:
                    sub_start = ''.join([' ' for _ in range(start.count(' '))]) + indent + str(i) + '.'
                item.print(State, start=sub_start)


def get_task(Tasks, task_pointer_list):
    task = Tasks[task_pointer_list[0]]
    for num in task_pointer_list[1:]:
        task = task.itemList[num]
    return task


def display_tasks(State, Tasks):
    for _ in range(15):
        print('')
    sprint('---------------------------------------------------------------------------------------------------------')
    for i, task in enumerate(Tasks):
        task.print(State, start=' ' + str(i) + '.')
    sprint('---------------------------------------------------------------------------------------------------------')


def swap_tasks(Tasks, task_pointer_list, direction):
    pointer = task_pointer_list[-1]
    if len(task_pointer_list) == 1:
        if 0 <= pointer + direction < len(Tasks):
            temp = Tasks[pointer]
            Tasks[pointer] = Tasks[pointer + direction]
            Tasks[pointer + direction] = temp
    else:
        if 0 <= pointer + direction < len(Tasks):
            parent_task = get_task(Tasks, task_pointer_list[:-1])
            temp = parent_task.itemList[pointer]
            parent_task.itemList[pointer] = parent_task.itemList[pointer + direction]
            parent_task.itemList[pointer + direction] = temp
    task_pointer_list[-1] = pointer + direction
    return task_pointer_list


def load_data(taskfile):
    if not path.isfile(taskfile):
        State = {"display_done": True, "display_taken_care_of": True, "mark_priority": True, "priority_only": False,
                 "display_irrelevant": True, 'expand_all': True, 'verbose': False}
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


def parse_command(cmd):
    cmd = cmd.lower()

    cmd_list = cmd.split(' ')
    opcode = next(word for word in cmd_list if not word.isnumeric())
    cmd_list.remove(opcode)

    src_pointer = []
    cmd_offset = 0
    if len(cmd_list) == 0:
        data = ''
    else:
        while cmd_offset < len (cmd_list) and cmd_list[cmd_offset].isnumeric():
            src_pointer.append(int(cmd_list[cmd_offset]))
            cmd_offset += 1
        data = ' '.join(cmd_list[cmd_offset:])
    src_pointer = '' if len(src_pointer) == 0 else src_pointer
    cmd_dict = {'opcode': opcode, 'src_pointer': src_pointer, 'data': data}

    return cmd_dict


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

    elif cmd_dict['opcode'] == 'hh':
        State['mark_priority'] = not State['mark_priority']

    elif cmd_dict['opcode'] == 'e':
        State['expand_all'] = not State['expand_all']
        for task in Tasks:
            task.set_expension(State['expand_all'])

    elif cmd_dict['opcode'] == 'v':
        State['verbose'] = not State['verbose']

    elif cmd_dict['opcode'] == 'w' or cmd_dict['opcode'] == 's':
        direction = - 1 if cmd_dict['opcode'] == 'w' else 1
        cmd_dict['src_pointer'] = swap_tasks(Tasks, cmd_dict['src_pointer'], direction)

    else:
        new_task = ' '.join([cmd_dict['opcode'], cmd_dict['src_pointer'], cmd_dict['data']])
        Tasks.append(Task(new_task))


def execute_command_specific(cmd_dict, Tasks):
    task = get_task(Tasks, cmd_dict['src_pointer'])

    if cmd_dict['opcode'] == 'del':
        pointer = cmd_dict['src_pointer'][-1]
        if len(cmd_dict['src_pointer']) == 1:
            del Tasks[pointer]
        else:
            parent_task = get_task(Tasks, cmd_dict['src_pointer'][:-1])
            del parent_task.itemList[pointer]

    elif cmd_dict['opcode'] == 'd':
        task.status['done'] = not task.status['done']
        task.done_date = date.today()

    elif cmd_dict['opcode'] == 'e':
        task.expendItems = not task.expendItems

    elif cmd_dict['opcode'] == 'a':
        task.add_item(cmd_dict['data'])

    elif cmd_dict['opcode'] == 'h':
        task.status['priority'] = not task.status['priority']

    elif cmd_dict['opcode'] == 'g':
        task.status['taken_care_of'] = not task.status['taken_care_of']

    elif cmd_dict['opcode'] == 'f':
        task.status['irrelevant'] = not task.status['irrelevant']

    elif cmd_dict['opcode'] == 'w' or cmd_dict['opcode'] == 's':
        direction = - 1 if cmd_dict['opcode'] == 'w' else 1
        cmd_dict['src_pointer'] = swap_tasks(Tasks, cmd_dict['src_pointer'], direction)

    elif cmd_dict['opcode'] == 'c':
        if cmd_dict['data'].startswith('b'):
            color = Fore.BLUE
        # elif cmd_dict['data'].startswith('r'):
        #     color = Fore.RED
        elif cmd_dict['data'].startswith('m'):
            color = Fore.LIGHTMAGENTA_EX
        elif cmd_dict['data'].startswith('c'):
            color = Fore.CYAN
        # elif cmd_dict['data'].startswith('y'):
        #     color = Fore.YELLOW
        # elif cmd_dict['data'].startswith('g'):
        #     color = Fore.GREEN
        elif cmd_dict['data'].startswith('w'):
            color = Fore.WHITE
        elif cmd_dict['data'].startswith('k'):
            color = Fore.BLACK
        else:
            color = Fore.WHITE

        task.set_color(color)

    else:
        task.name = ' '.join([cmd_dict['opcode'], cmd_dict['data']])


def main():
    taskfile = "taskfile"
    State, Tasks = load_data(taskfile)
    sprint('welcome to TODO list:')
    display_tasks(State, Tasks)

    while True:
        cmd = input()
        cmd_dict = parse_command(cmd)

        if len(cmd_dict['src_pointer']) == 0:
            execute_command_general(cmd_dict, State, Tasks)
        else:
            execute_command_specific(cmd_dict, Tasks)

        display_tasks(State, Tasks)
        save_data(taskfile, State, Tasks)


if __name__ == '__main__':
    main()
