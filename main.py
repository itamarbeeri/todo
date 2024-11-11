#!/usr/bin/env python3

import os
import sys
from datetime import date
from data_manager import save_data, load_data
from config import opcode_dict, color_dict, HELP_TEXT, CROSS_SECTION_LINE, UNDERLINE_CODE, RESET_ALL_CODE, sys_print, \
    FG_COLOR_DONE, FG_COLOR_TAKEN_CARE_OF, FG_COLOR_DONE_IRRELEVANT

os.system('')

def update_tasks(Tasks):
    for task in Tasks:
        task.update_status()

def print_state(State):
    sys_print(f'State is: \n')
    for key, value in State.items():
        sys_print(f'{key}: {value}')
    sys_print('\npress enter to continue.\n')
    input()

def print_instructions(State):

    sys_print(HELP_TEXT)

    sys_print('optional colors are:')
    for color_letter, color_code in color_dict.items():
        print(color_code + color_letter, end=', ')

    print(RESET_ALL_CODE)
    sys_print('\nGood luck! press enter to continue.\n')
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
        if self.period['activationDay'] == 0:
            if self.status['done'] and self.status['priority']:
                if today.month > self.done_date.month:
                    self.status['priority'] = False
                    self.status['urgent'] = False
        else:
            if self.period['lastActivation'].month != today.month:
                if int(self.period['activationDay']) <= today.day or self.period['lastActivation'].month + 1 < today.month:
                    self.period['lastActivation'] = today
                    self.set_status('done', False, propogate=False)

        for subTask in self.subTasks:
            subTask.update_status()

    def add_subTask(self, name):
        self.subTasks.append(Task(name, color=self.color))

    def set_color(self, color):
        for subTask in self.subTasks:
            subTask.set_color(color)
        self.color = color

    def set_status(self, key, val, propogate=False):
        self.status[key] = val

        if propogate:
            for subTask in self.subTasks:
                subTask.set_status(key, val, propogate)

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
        if State['display_urgent'] is True and self.status['urgent'] is False:
            visible = False
        elif State['display_priority'] is True and self.status['priority'] is False:
            visible = False
        elif State['display_irrelevant'] is False and self.status['irrelevant'] is True:
            visible = False
        elif State['display_done'] is False and self.status['done'] is True:
            visible = False
        elif State['display_taken_care_of'] is False and self.status['taken_care_of'] is True:
            visible = False
        else:
            visible = True

        bg_color = ''
        fg_color = self.color
        for key, val in self.status.items():
            if val is True:
                bg_color, fg_color = color_scheme(key, self.color)
                break
        fg_color = self.color if fg_color == '' or State['display_urgent'] is True else fg_color

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
        expanded_task_status += RESET_ALL_CODE + f' /{len(self.subTasks)})'
        offset = '{:>' + str(max([165 - msg_length, msg_length + 1])) + '}'
        verbose = offset.format(f'{dates}, {expanded_task_status}') if State['verbose'] else ''

        appendix = end + verbose + RESET_ALL_CODE
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
                if State['display_urgent'] or State['display_priority']:
                    sub_start = start + str(i) + '.'
                else:
                    sub_start = ''.join([' ' for _ in range(start.count(' '))]) + '    ' + str(i) + '.'
                subTask.print(State, start=sub_start)


class Command:
    def __init__(self, raw_cmd, State):
        self.cmd, self.next_raw_cmd = self.commad_separator(raw_cmd)
        self.opcode = self.extract_opcode()
        self.task_location = self.extract_task_location(State)
        self.data = self.extract_data()

    def commad_separator(self, raw_cmd):
        split_cmd = raw_cmd.split(';')
        cmd = split_cmd[0].lstrip().split(' ')
        next_raw_cmd = None if len(split_cmd[1:]) == 0 else ';'.join(split_cmd[1:])

        return cmd, next_raw_cmd

    def extract_opcode(self):
        return next((word for word in self.cmd if not word.isnumeric()), None)

    def extract_task_location(self, State):
        task_location = State['constant_parent_task'].copy()
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
        cmd = self.cmd.copy()

        if self.opcode:
            cmd.remove(self.opcode)
        for i in self.task_location:
            if str(i) in cmd:
                cmd.remove(str(i))

        return ' '.join(cmd)

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
        sys_print(CROSS_SECTION_LINE)
        for i, task in enumerate(Tasks):
            task.print(State, start=' ' + str(i) + '.')
        sys_print(CROSS_SECTION_LINE)
    else:
        State['display'] = True


def color_scheme(status_key, original_color=''):
    bg_color = ''
    fg_color = ''

    if status_key == 'done':
        fg_color = FG_COLOR_DONE

    elif status_key == "taken_care_of":
        fg_color = FG_COLOR_TAKEN_CARE_OF

    elif status_key == "irrelevant":
        bg_color = FG_COLOR_DONE_IRRELEVANT

    elif status_key == 'urgent':
        fg_color = UNDERLINE_CODE + original_color

    return bg_color, fg_color


def get_task(Tasks, task_pointer_list):
    task = Tasks[task_pointer_list[0]]
    for num in task_pointer_list[1:]:
        task = task.subTasks[num]
    return task


def execute_command_general(cmd, State, Tasks):
    if cmd.opcode == 'quit' or cmd.opcode == 'exit':
        sys.exit()

    elif cmd.opcode == 'state':
        print_state(State)

    elif cmd.opcode == 'help':
        print_instructions(State)

    elif cmd.opcode in opcode_dict:
        property_name = 'display_' + opcode_dict[cmd.opcode]
        State[property_name] = not State[property_name]

        if cmd.opcode == 'u' or cmd.opcode == 'h':
            State['display_urgent'] = False if cmd.opcode == 'h' else State['display_urgent']
            State['display_priority'] = False if cmd.opcode == 'u' else State['display_priority']
            State['expand_all'] = True
            for task in Tasks:
                task.set_expension(State['expand_all'])

    elif cmd.opcode == 'e':
        State['display_urgent'], State['display_priority'] = False, False
        State['expand_all'] = not State['expand_all']
        for task in Tasks:
            task.set_expension(State['expand_all'])

    elif cmd.opcode == 'v':
        State['verbose'] = not State['verbose']

    elif cmd.opcode == 'c':
        State['display'] = False
        sys_print('arguments for color command are:')
        for key, val in color_dict.items():
            print(f"{val}{key}{RESET_ALL_CODE}")

    elif cmd.opcode == 'const':
        State['constant_parent_task'] = list()

    else:
        new_task = ' '.join([cmd.opcode, cmd.data])
        Tasks.append(Task(new_task))


def execute_command_specific(cmd, State, Tasks):
    task = get_task(Tasks, cmd.task_location)

    if cmd.opcode == None:
        State['expand_all'] = False
        State['display_priority'] = False
        State['display_urgent'] = False
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

    elif cmd.opcode == 'dd':
        current_val = task.status['done']
        task.set_status('done', not current_val, propogate=True)

    elif cmd.opcode == 'e':
        State['display_urgent'], State['display_priority'] = False, False
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

    elif cmd.opcode == 'const':
        State['constant_parent_task'] = cmd.data

    else:
        if not cmd.opcode in opcode_dict:
            task.add_subTask(' '.join([cmd.opcode, cmd.data]))


def main():
    sys_print('welcome to TODO list:')

    State, Tasks = load_data()
    update_tasks(Tasks)
    display_tasks(State, Tasks)

    while True:
        try:
            cmd = Command(input(), State)
            cmd.execute(State, Tasks)
            display_tasks(State, Tasks)
            save_data(State, Tasks)

        except SystemExit:
            save_data(State, Tasks)
            sys_print('good bye.')
            sys.exit()

        except:
            State["display_urgent"] = False
            sys_print('error.')


if __name__ == '__main__':
    main()

# pyinstaller --onefile main.py

