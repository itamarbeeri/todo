#!/usr/bin/env python3

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

    def addItem(self, item):
        self.itemList.append(item)

    def print(self, start=None):
        bg_color = Back.GREEN if self.isDone is True else Back.BLACK
        start = '' if start is None else str(start)
        print(f"{bg_color}{self.color}{start} {self.name}")
        if self.expendItems is True:
            for item in self.expendItems:
                item.print(start='     ')


def print_instructions():
    def sprint(text):
        print(f"{Fore.LIGHTRED_EX}{text}")

    sprint('Welcome to TODO list.')
    sprint('..')

    sprint('Create a new task - type n aasdasd where aasdasd is the task name.')
    sprint('Choose an existing task - type t## where ## is the task number.')
    sprint('Choose a sub task - after choosing a task, type st## where ## is the subtask number.')
    sprint('Edit a choosen task:')
    sprint(' - d to toggle Done/UnDone')
    sprint(' - e to toggle sub items expantion display')
    sprint(' - c followed by color to change color - c ,b ,r ,m for cyan, blue, red and magenta. e.g: c c for cyan.')
    sprint(' - i followed by color to change color.')
    sprint(' - arrows to move the task up/down in task list')
    sprint(' - del to delete task.')
    sprint('Save changes - type s.')
    sprint('Quit - type q')

    sprint('..')
    sprint('Done tasks are colored in green.')
    sprint('Good luck!')

def load_tasks():
    # TODO: build
    return []

def save_tasks():
    # TODO: build
    return []

taskPointer = None
subTaskPointer = None
Tasks = load_tasks()

def main():
    print(f"{Fore.LIGHTRED_EX} welcome to TODO list:")

    while True:
        cmd = input()
        if parse_command(cmd):
            for i, task in enumerate(Tasks):
                task.print(start=' ' + str(i) + '. ')

        print(f'{Fore.LIGHTRED_EX} task pointer is: {taskPointer}. sub task pointer is: {subTaskPointer}')


def parse_command(cmd):
    global taskPointer
    global subTaskPointer
    cmd = cmd.lower()
    isUpdate = False

    if cmd == 'help':
        print_instructions()
        isUpdate = False

    elif cmd.startswith('n'):
        name = cmd[2:]
        taskPointer = len(Tasks)
        subTaskPointer = None
        Tasks.append(Task(name))
        isUpdate = True

    elif cmd.startswith('s'):
        # TODO: save
        isUpdate = False

    elif cmd.startswith('q'):
        # TODO: quit
        isUpdate = False

    elif cmd.startswith('t') and cmd[1:].isnumeric():
        num = int(cmd[1:])
        if len(Tasks) < num:
            print(f'Task number {num} doesnt exist.')
        else:
            taskPointer = num
            subTaskPointer = None
        isUpdate = False

    elif cmd.startswith('st') and cmd[2:].isnumeric():
        num = int(cmd[2:])
        if len(Tasks.itemList) < num:
            print(f'Sub task number {num} for task number {taskPointer} doesnt exist.')
        else:
            subTaskPointer = num
        isUpdate = False

    elif cmd == 'd' and taskPointer is not None:
        if subTaskPointer is None:
            Tasks[taskPointer].isDone = not Tasks[taskPointer].isDone
        else:
            Tasks[taskPointer].itemList[subTaskPointer].isDone = not Tasks[taskPointer].itemList[subTaskPointer].isDone
        isUpdate = True


    elif cmd == 'e' and taskPointer is not None:
        if subTaskPointer is None:
            Tasks[taskPointer].expendItems = not Tasks[taskPointer].expendItems
        isUpdate = True

    elif cmd.startswith('c') and taskPointer is not None:
        if cmd[2:].startswith('b'):
            color = Fore.BLUE
        elif cmd[2:].startswith('r'):
            color = Fore.RED
        elif cmd[2:].startswith('m'):
            color = Fore.LIGHTMAGENTA_EX
        elif cmd[2:].startswith('c'):
            color = Fore.CYAN
        else:
            color = Fore.YELLOW

        if subTaskPointer is None:
            Tasks[taskPointer].color = color
        else:
            Tasks[taskPointer].itemList[subTaskPointer].color = color
        isUpdate = True


    elif cmd == 'i' and taskPointer is not None:
        # TODO: add sub item
        isUpdate = True

    # TODO: arrows
    # TODO: del

    else:
        print(f'{cmd} is an invalid command.')

    return isUpdate

if __name__ == '__main__':
    main()

