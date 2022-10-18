#!/usr/bin/env python3

import pickle
from os import path

import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

exp = True
task_pointer_list = []
indent = '    '
hide_done = False

def sprint(text):
    print(f"{Fore.LIGHTRED_EX}{text}")


def print_instructions():
    sprint('Welcome to TODO list.')
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
    def __init__(self, name, color=Fore.WHITE, expendItems=True, display=True):
        self.name = name
        self.status = {'done': False, 'taken_care_of': False, 'priority': False, 'irrelevant': False}
        self.itemList = []
        self.color = color
        self.expendItems = expendItems

    def add_item(self, name):
        self.itemList.append(Task(name, color=self.color))

    def set_color(self, color):
        for item in self.itemList:
            if self.color == item.color:
                item.color = color
        self.color = color

    def set_expension(self, val):
        self.expendItems = val
        for item in self.itemList:
            item.set_expension(val)

    def change_display_status(self, status, val):
        if self.status == status:
            self.display = val
        for item in self.itemList:
            item.change_display_status(val)

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
            bg_color = Back.GREEN
            fg_color = Fore.BLACK + Style.BRIGHT

        elif self.status["taken_care_of"] is True:
            bg_color = Back.YELLOW
            fg_color = Fore.BLACK + Style.NORMAL

        elif self.status["irrelevant"] is True:
            bg_color = Back.LIGHTRED_EX
            fg_color = Fore.WHITE

        elif self.status["priority"] is True:
            if State["mark_priority"] is True:
                bg_color = Back.LIGHTMAGENTA_EX
                fg_color = Fore.BLACK + Style.NORMAL
            else:
                bg_color = Back.BLACK
                fg_color = self.color

        else:
            bg_color = Back.BLACK
            fg_color = self.color

        return fg_color, bg_color, visible

    def print(self, State, start=None):
        global indent
        fg_color, bg_color, visible = self.get_display_params(State)
        if visible is True:
            start = '' if start is None else str(start)
            end = '' if self.expendItems is True else ' ...'
            print(f"{bg_color}{fg_color}{start} {self.name}{end}")

            if self.expendItems is True:
                for i, item in enumerate(self.itemList):
                    sub_start = ''.join([' ' for _ in range(start.count(' '))]) + indent + str(i) + '.'
                    item.print(State, start=sub_start)


def get_task(Tasks, task_pointer_list):
    task = Tasks[task_pointer_list[0]]
    for num in task_pointer_list[1:]:
        task = task.itemList[num]
    return task


def display_tasks(State, Tasks):
    for i, task in enumerate(Tasks):
        task.print(State, start=' ' + str(i) + '.')


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
                 "display_irrelevant": True, 'expand_all': True}
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


def parse_command(cmd, State, Tasks):
    global exp, hide_done, task_pointer_list, highlight_only_flag
    cmd = cmd.lower()
    isUpdate = True

    if cmd == 'help':
        print_instructions()

    elif cmd == 'd':
        State['display_done'] = not State['display_done']

    elif cmd == 'f':
        State['display_irrelevant'] = not State['display_irrelevant']

    elif cmd == 'g':
        State['display_taken_care_of'] = not State['display_taken_care_of']

    elif cmd == 'h':
        State['priority_only'] = not State['priority_only']

    elif cmd == 'hh':
        State['mark_priority'] = not State['mark_priority']

    elif cmd == 'e':
        State['expand_all'] = not State['expand_all']
        for task in Tasks:
            task.set_expension(State['expand_all'])

    elif cmd == 'w' or cmd == 's':
        direction = - 1 if cmd == 'w' else 1
        task_pointer_list = swap_tasks(Tasks, task_pointer_list, direction)

    elif not cmd[0].isnumeric():
        Tasks.append(Task(cmd))

    else:
        cmd_list = cmd.split(' ')
        cmd_offset = 0
        task_pointer_list = []
        while cmd_list[cmd_offset].isnumeric():
            task_pointer_list.append(int(cmd_list[cmd_offset]))
            cmd_offset += 1
        opcode = cmd_list[cmd_offset]
        data = ' '.join(cmd_list[cmd_offset + 1:])

        try:
            task = get_task(Tasks, task_pointer_list)

        except:
            sprint(f"ERROR! {task_pointer_list} is an invalid task number!.")
            isUpdate = False

        else:
            try:
                execute_command(Tasks, task_pointer_list, task, opcode, data)
            except:
                sprint(f"ERROR! cant execute command.")
                isUpdate = False
    return isUpdate


def execute_command(Tasks, task_pointer_list, task, opcode, data):
    if opcode == 'del':
        pointer = task_pointer_list[-1]
        if len(task_pointer_list) == 1:
            del Tasks[pointer]
        else:
            parent_task = get_task(Tasks, task_pointer_list[:-1])
            del parent_task.itemList[pointer]

    elif opcode == 'd':
        task.status['done'] = not task.status['done']

    elif opcode == 'e':
        task.expendItems = not task.expendItems

    elif opcode == 'a':
        task.add_item(data)

    elif opcode == 'h':
        task.status['priority'] = not task.status['priority']

    elif opcode == 'g':
        task.status['taken_care_of'] = not task.status['taken_care_of']

    elif opcode == 'f':
        task.status['irrelevant'] = not task.status['irrelevant']

    elif opcode == 'w' or opcode == 's':
        direction = - 1 if opcode == 'w' else 1
        task_pointer_list = swap_tasks(Tasks, task_pointer_list, direction)

    elif opcode == 'c':
        if data.startswith('b'):
            color = Fore.BLUE
        elif data.startswith('r'):
            color = Fore.RED
        elif data.startswith('m'):
            color = Fore.LIGHTMAGENTA_EX
        elif data.startswith('c'):
            color = Fore.CYAN
        elif data.startswith('y'):
            color = Fore.YELLOW
        elif data.startswith('g'):
            color = Fore.GREEN
        elif data.startswith('w'):
            color = Fore.WHITE
        elif data.startswith('k'):
            color = Fore.BLACK
        else:
            color = Fore.WHITE

        task.set_color(color)

    else:
        task.name = ' '.join([opcode, data])


def main():
    taskfile = "taskfile"
    State, Tasks = load_data(taskfile)
    sprint('welcome to TODO list:')
    display_tasks(State, Tasks)

    while True:
        cmd = input()
        if parse_command(cmd, State, Tasks):
            display_tasks(State, Tasks)
        save_data(taskfile, State, Tasks)


if __name__ == '__main__':
    main()
