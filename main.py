#!/usr/bin/env python3

import pickle
from os import path

import colorama
from colorama import Fore, Back

colorama.init(autoreset=True)


class Task:
    def __init__(self, name, isDone=False, color=Fore.YELLOW, expendItems=False):
        self.name = name
        self.isDone = isDone
        self.color = color
        self.itemList = []
        self.expendItems = expendItems

    def addItem(self, name):
        self.itemList.append(Task(name, color=self.color))

    def setColor(self, color):
        for item in self.itemList:
            if self.color == item.color:
                item.color = color
        self.color = color

    def print(self, start=None):
        bg_color = Back.GREEN if self.isDone is True else Back.BLACK
        start = '' if start is None else str(start)
        print(f"{bg_color}{self.color}{start} {self.name}")
        if self.expendItems is True:
            for item in self.itemList:
                item.print(start='     ')


def sprint(text):
    print(f"{Fore.LIGHTRED_EX}{text}")


def print_instructions():
    sprint('Welcome to TODO list.')
    sprint('..')

    sprint('Create a new task - type the task name.')
    sprint('Edit a task - type the task number followed by command')
    sprint('  d (to toggle Done/UnDone)')
    sprint('  e (to toggle sub items expantion display)')
    sprint('  c (change task color) followed by color to change color - c ,b ,r ,m for cyan, blue, red and magenta.')
    sprint('  a (add sub task) followed by sub task name')
    sprint('  del to delete task.')
    sprint("Example: '6 c m' -> color task 6 in magenta. '2 d' toggle task 2 done status")

    sprint('..')
    sprint('Good luck!')


def display_tasks(Tasks):
    for i, task in enumerate(Tasks):
        task.print(start=' ' + str(i) + '. ')


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
    cmd = cmd.lower()
    # TODO: fix sub tasks colors

    if cmd == 'help':
        print_instructions()
        isUpdate = False

    elif not cmd[0].isnumeric():
        Tasks.append(Task(cmd))
        isUpdate = True

    else:
        cmd_list = cmd.split(' ')
        task_num = int(cmd_list[0])
        subtask_num = int(cmd_list[1]) if cmd_list[1][0].isnumeric() else None
        opcode_offset = 1 if subtask_num is None else 2
        opcode = cmd_list[opcode_offset]
        data = ' '.join(cmd_list[opcode_offset + 1:])
        if len(Tasks) < task_num:
            sprint(f"{task_num} is an invalid task number for {len(Tasks)} tasks.")
            isUpdate = False
        else:
            isUpdate = execute_command(Tasks, task_num, subtask_num, opcode, data)

    return isUpdate


def execute_command(Tasks, task_num, subtask_num, opcode, data):
    if opcode == 'del':
        # TODO: replace the following 4 lines with set attribute: Tasks[task_num].set(att, value, subtask_num)
        if subtask_num is None:
            del Tasks[task_num]
        else:
            del Tasks[task_num].itemList[subtask_num]
        isUpdate = True

    elif opcode == 'd':
        if subtask_num is None:
            Tasks[task_num].isDone = not Tasks[task_num].isDone
        else:
            Tasks[task_num].itemList[subtask_num].isDone = not Tasks[task_num].itemList[subtask_num].isDone
        isUpdate = True

    elif opcode == 'e':
        Tasks[task_num].expendItems = not Tasks[task_num].expendItems
        isUpdate = True

    elif opcode == 'a':
        Tasks[task_num].addItem(data)
        isUpdate = True

    elif opcode == 'w' or opcode == 's':
        direction = - 1 if opcode == 'w' else 1
        if 0 <= task_num + direction < len(Tasks):
            temp = Tasks[task_num]
            Tasks[task_num] = Tasks[task_num + direction]
            Tasks[task_num + direction] = temp
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
        else:
            color = Fore.YELLOW

        if subtask_num is None:
            Tasks[task_num].setColor(color)
        else:
            Tasks[task_num].itemList[subtask_num].setColor(color)
        isUpdate = True

    else:
        sprint(f"{opcode} is an invalid operation. try 'help''")
        isUpdate = False

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
