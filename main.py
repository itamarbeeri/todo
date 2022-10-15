#!/usr/bin/env python3

import pickle
from os import path

import colorama
from colorama import Fore, Back

colorama.init(autoreset=True)

exp = True
hide_done = True
task_pointer_list = []
indent = '    '

class Task:
    def __init__(self, name, isDone=False, color=Fore.WHITE, expendItems=True, display=True):
        self.name = name
        self.isDone = isDone
        self.color = color
        self.itemList = []
        self.expendItems = expendItems
        self.display = display

    def addItem(self, name):
        self.itemList.append(Task(name, color=self.color))

    def setColor(self, color):
        for item in self.itemList:
            if self.color == item.color:
                item.color = color
        self.color = color

    def set_expension(self, val):
        self.expendItems = val
        for item in self.itemList:
            item.set_expension(val)

    def set_display_done(self, val):
        if self.isDone is True:
            self.display = val
        for item in self.itemList:
            item.set_display_done(val)

    def print(self, start=None):
        global indent
        if self.display is True:
            bg_color = Back.LIGHTGREEN_EX if self.isDone is True else Back.BLACK
            start = '' if start is None else str(start)
            end = '' if self.expendItems is True else ' ...'
            print(f"{bg_color}{self.color}{start} {self.name}{end}")

            if self.expendItems is True:
                for i, item in enumerate(self.itemList):
                    sub_start = ''.join([' ' for _ in range(start.count(' '))]) + indent + str(i) + '.'
                    item.print(start=sub_start)


def sprint(text):
    print(f"{Fore.LIGHTRED_EX}{text}")


def print_instructions():
    sprint('Welcome to TODO list.')
    sprint('..')

    sprint('Create a new task - type the task name.')
    sprint('expand/collapse all press x')
    sprint('hide/display all done tasks press d')
    sprint('Edit a task - type the task number followed by command')
    sprint('  d (to toggle Done/UnDone)')
    sprint('  e (to toggle sub items expantion display)')
    sprint('  c (change task color) followed by color to change color - c ,b ,r ,m, w ,g for cyan, blue...')
    sprint('  a (add sub task) followed by sub task name')
    sprint('  del to delete task.')
    sprint("Example: '6 c m' -> color task 6 in magenta. '2 d' toggle task 2 done status")

    sprint('..')
    sprint('Good luck!')

def get_task(Tasks, task_pointer_list):
    task = Tasks[task_pointer_list[0]]
    for num in task_pointer_list[1:]:
        task = task.itemList[num]
    return task

def display_tasks(Tasks):
    for i, task in enumerate(Tasks):
        task.print(start=' ' + str(i) + '.')


def swap_tasks(Tasks, task_pointer_list, dir):
    pass

def load_tasks(taskfile):
    if not path.isfile(taskfile):
        return []
    with open(taskfile, "rb") as fp:
        Tasks = pickle.load(fp)
    return Tasks


def save_tasks(taskfile, Tasks):
    with open(taskfile, "wb") as fp:
        pickle.dump(Tasks, fp)


def parse_command(cmd, Tasks):
    global exp, hide_done, task_pointer_list
    cmd = cmd.lower()
    # TODO: fix sub tasks colors

    if cmd == 'help':
        print_instructions()
        isUpdate = False

    elif cmd == 'x':
        exp = not exp
        for task in Tasks:
            task.set_expension(exp)
        isUpdate = True

    elif cmd == 'd':
        hide_done = not hide_done
        for task in Tasks:
            task.set_display_done(hide_done)
        isUpdate = True

    elif cmd == 'w' or cmd == 's':
        direction = - 1 if cmd == 'w' else 1
        task_pointer_list = swap_tasks(Tasks, task_pointer_list, direction)
        isUpdate = True

    elif not cmd[0].isnumeric():
        Tasks.append(Task(cmd))
        isUpdate = True

    else:
        cmd_list = cmd.split(' ')
        cmd_offset = 0
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
                isUpdate = execute_command(Tasks, task_pointer_list, task, opcode, data)
            except:
                sprint(f"ERROR! cant execute command.")
                isUpdate = False
    return isUpdate


def execute_command(Tasks, task_pointer_list, task, opcode, data):

    if opcode == 'del':
        del task
        isUpdate = True

    elif opcode == 'd':
        task.isDone = not task.isDone
        isUpdate = True

    elif opcode == 'e':
        task.expendItems = not task.expendItems
        isUpdate = True

    elif opcode == 'a':
        task.addItem(data)
        isUpdate = True

    elif opcode == 'w' or opcode == 's':
        direction = - 1 if opcode == 'w' else 1
        task_pointer_list = swap_tasks(Tasks, task_pointer_list, direction)
        isUpdate = True

    elif opcode == 'c':
        if data.startswith('b'):
            color = Fore.BLUE
        elif data.startswith('r'):
            color = Fore.RED
        elif data.startswith('m'):
            color = Fore.LIGHTMAGENTA_EX
        elif data.startswith('c'):
            color = Fore.CYAN
        elif data.startswith('w'):
            color = Fore.WHITE
        elif data.startswith('g'):
            color = Fore.GREEN
        else:
            color = Fore.YELLOW

        task.setColor(color)
        isUpdate = True

    else:
        task.name = ' '.join([opcode, data])
        isUpdate = True

    return isUpdate


def main():
    taskfile = "taskfile"
    Tasks = load_tasks(taskfile)
    sprint('welcome to TODO list:')
    display_tasks(Tasks)

    while True:
        cmd = input()
        if parse_command(cmd, Tasks):
            display_tasks(Tasks)
        save_tasks(taskfile, Tasks)


if __name__ == '__main__':
    main()
