#!/usr/bin/env python3

import copy
import math
import os
import re
import sys
from datetime import date
from time import time

from config import opcode_dict, color_dict, HELP_TEXT, CROSS_SECTION_LINE, UNDERLINE_CODE, RESET_ALL_CODE, sys_print, \
    FG_COLOR_DONE, FG_COLOR_TAKEN_CARE_OF, FG_COLOR_DONE_IRRELEVANT, MAX_UNSAVED_COMMANDS, MAX_UNSAVED_TIME, \
    MAX_UNDO_STEPS, initial_state
from data_manager import save_data, load_data

os.system('')

ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')


class LineCountingStream:
    def __init__(self, stream, state):
        self.stream = stream
        self.state = state
        self._col = 0

    def write(self, text):
        self.stream.write(text)
        try:
            cols = os.get_terminal_size().columns
        except OSError:
            cols = 80
        for segment in ANSI_ESCAPE_RE.split(text):
            for char in segment:
                if char == '\n':
                    self.state['lines_since_last_erase'] += 1
                    self._col = 0
                elif char == '\r':
                    self._col = 0
                else:
                    self._col += 1
                    if self._col >= cols:
                        self.state['lines_since_last_erase'] += 1
                        self._col = 0

    def flush(self):
        self.stream.flush()

    def fileno(self):
        return self.stream.fileno()


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
        self.status = {'done': False, 'taken_care_of': False, 'irrelevant': False, 'urgent': False, 'priority': False, 'agenda': False}
        self.period = {'activationDay': 0, 'lastActivation': date.today()}

    def update_status(self):
        today = date.today()
        if self.period['activationDay'] == 0:
            if self.status['done'] and self.status['priority']:
                if today.month > self.done_date.month:
                    self.status['priority'] = False
                    self.status['urgent'] = False
        else:
            last = self.period['lastActivation']
            months_passed = (today.year - last.year) * 12 + (today.month - last.month)
            if months_passed > 0:
                if int(self.period['activationDay']) <= today.day or months_passed > 1:
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

        if key in ('done', 'irrelevant') and val is True:
            self.status['agenda'] = False

    def set_expension(self, val):
        self.expand = val
        for subTask in self.subTasks:
            subTask.set_expension(val)

    def count_status(self):
        counter = {'regular': 0, 'done': 0, 'taken_care_of': 0, 'priority': 0, 'urgent': 0, 'irrelevant': 0, 'agenda': 0}
        for subTask in self.subTasks:
            is_regular = True
            for key, val in subTask.status.items():
                counter[key] += val
                is_regular = False if val is True else is_regular
            counter['regular'] += is_regular
        return counter

    def get_display_params(self, State):
        if State.get('pinned_task') is self:
            return self.color, '', True

        if State['display_urgent'] is True and self.status['urgent'] is False:
            visible = False
        elif State['display_priority'] is True and self.status['priority'] is False:
            visible = False
        elif State['display_agenda'] is True and self.status['agenda'] is False:
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

        task_status = '' if len(self.subTasks) == 0 else f'({len(self.subTasks) - status["done"]}/{len(self.subTasks)})'
        expand_sign = '' if len(self.subTasks) == 0 else " ..." if self.expand is False else ':'
        dates = str(self.creation_date) + '-' + str(self.done_date)

        end = task_status + expand_sign
        msg_length += len(end)

        expanded_task_status = '('
        for key, val in status.items():
            bg, fg = color_scheme(key)
            expanded_task_status += bg + fg + str(val) + ','
        expanded_task_status = expanded_task_status[:-1]
        expanded_task_status += RESET_ALL_CODE + f' /{len(self.subTasks)})'
        offset = '{:>' + str(max([165 - msg_length, msg_length + 1])) + '}'
        verbose = offset.format(f'{dates}, {expanded_task_status}') if State['verbose'] else ''

        appendix = end + verbose + RESET_ALL_CODE
        return appendix

    def print(self, State, start=None):
        fg_color, bg_color, visible = self.get_display_params(State)

        if visible is True:
            start = '' if start is None else str(start)
            end = self.build_appendix(State, len(start) + 1 + len(self.name))
            start_color = fg_color.replace(UNDERLINE_CODE, '') if UNDERLINE_CODE in fg_color else fg_color
            print(f"{bg_color}{start_color}{start} {fg_color}{self.name} {end}")

        if self.expand is True:
            for i, subTask in enumerate(self.subTasks):
                subTask.print(State, start='  ' + start + str(i) + '.')


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
        State['pinned_task'] = None
        State['detail_info'] = []

        if self.opcode not in ('z', 'y'):
            State['undo_stack'].append(copy.deepcopy(Tasks))
            if len(State['undo_stack']) > MAX_UNDO_STEPS:
                State['undo_stack'].pop(0)
            State['redo_stack'].clear()

        if len(self.task_location) == 0:
            execute_command_general(self, State, Tasks)
        else:
            execute_command_specific(self, State, Tasks)

        if self.next_raw_cmd is not None:
            cmd = Command(self.next_raw_cmd, State)
            cmd.execute(State, Tasks)

        State['prv_src_pointer'] = self.task_location


def collect_agenda_tasks(Tasks):
    result = []
    def recurse(task):
        if task.status['agenda'] and not task.status['done'] and not task.status['irrelevant']:
            result.append(task)
        for sub in task.subTasks:
            recurse(sub)
    for task in Tasks:
        recurse(task)
    return result


def sync_agenda_order(State, Tasks):
    all_agenda = collect_agenda_tasks(Tasks)
    State['agenda_order'] = [t for t in State['agenda_order'] if t in all_agenda]
    for t in all_agenda:
        if t not in State['agenda_order']:
            State['agenda_order'].append(t)


def find_task_path(task, Tasks):
    def search(target, task_list, path):
        for i, t in enumerate(task_list):
            if t is target:
                return path + [i]
            result = search(target, t.subTasks, path + [i])
            if result is not None:
                return result
        return None
    return search(task, Tasks, [])


def _erase_lines(n):
    out = sys.__stdout__ if sys.__stdout__ is not None else sys.stdout
    out.write(f'\033[{n}A\033[J')
    out.flush()


def display_tasks(State, Tasks):
    if State['display']:
        lines = State['lines_since_last_erase']
        if lines > 0:
            _erase_lines(lines)
        State['lines_since_last_erase'] = 0

        if State['display_agenda']:
            sys_print('[ agenda ]')
        elif State['display_urgent']:
            sys_print('[ urgent ]')
        elif State['display_priority']:
            sys_print('[ priority ]')
        elif State.get('pinned_task') is not None:
            sys_print(f'[ {State["pinned_task"].name} ]')
        for line in State.get('detail_info', []):
            sys_print(line)
        if State['unsaved_command_counter'] > 0:
            sys_print(f'* unsaved changes ({State["unsaved_command_counter"]})')
        sys_print(CROSS_SECTION_LINE)
        if State['display_agenda']:
            sync_agenda_order(State, Tasks)
            for task in State['agenda_order']:
                fg_color, bg_color, _ = task.get_display_params(State)
                path = find_task_path(task, Tasks)
                start_str = ' ' + '.'.join(str(i) for i in path) + '.' if path else ' ?.'
                end = task.build_appendix(State, len(start_str) + 1 + len(task.name))
                start_color = fg_color.replace(UNDERLINE_CODE, '') if UNDERLINE_CODE in fg_color else fg_color
                print(f"{bg_color}{start_color}{start_str} {fg_color}{task.name} {end}")
        elif State.get('pinned_task') is not None:
            task = State['pinned_task']
            path = find_task_path(task, Tasks)
            start_str = ' ' + '.'.join(str(i) for i in path) + '.' if path else ' ?.'
            task.print(State, start=start_str)
        else:
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

    elif cmd.opcode == 'z':
        if State['undo_stack']:
            State['redo_stack'].append(copy.deepcopy(Tasks))
            Tasks[:] = State['undo_stack'].pop()
            State['unsaved_command_counter'] += 1

    elif cmd.opcode == 'y':
        if State['redo_stack']:
            State['undo_stack'].append(copy.deepcopy(Tasks))
            Tasks[:] = State['redo_stack'].pop()
            State['unsaved_command_counter'] += 1

    elif cmd.opcode == 'state':
        print_state(State)

    elif cmd.opcode == 'help':
        print_instructions(State)

    elif cmd.opcode in opcode_dict:
        property_name = 'display_' + opcode_dict[cmd.opcode]
        State[property_name] = not State[property_name]

        if cmd.opcode == 'u' or cmd.opcode == 'h' or cmd.opcode == 'a':
            State['display_urgent'] = State['display_urgent'] if cmd.opcode == 'u' else False
            State['display_priority'] = State['display_priority'] if cmd.opcode == 'h' else False
            State['display_agenda'] = State['display_agenda'] if cmd.opcode == 'a' else False
            State['expand_all'] = True
            for task in Tasks:
                task.set_expension(State['expand_all'])

    elif cmd.opcode == 's':
        save_data_wrapper(State, Tasks)

    elif cmd.opcode == 'e':
        in_filtered_view = (State['display_urgent'] or State['display_priority']
                            or State['display_agenda'] or State.get('pinned_task') is not None)
        State['display_urgent'] = False
        State['display_priority'] = False
        State['display_agenda'] = False
        State['pinned_task'] = None
        if in_filtered_view:
            State['expand_all'] = False
        else:
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
        State['unsaved_command_counter'] += 1


def execute_command_specific(cmd, State, Tasks):
    task = get_task(Tasks, cmd.task_location)

    if cmd.opcode == None:
        State['expand_all'] = False
        State['display_priority'] = False
        State['display_urgent'] = False
        State['display_agenda'] = False
        State['pinned_task'] = task
        State['detail_info'] = [str(task.status), str(task.period)]

        for Task in Tasks:
            Task.set_expension(False)
        task.set_expension(True)

    elif cmd.opcode in opcode_dict:
        propogate = True if cmd.opcode == 'f' else False
        property_name = opcode_dict[cmd.opcode]
        current_val = task.status[property_name]
        task.set_status(property_name, not current_val, propogate=propogate)

        if cmd.opcode == 'u':
            task.status['priority'] = True if task.status['urgent'] is True else task.status['priority']
        State['unsaved_command_counter'] += 1

    elif cmd.opcode == 'dd':
        current_val = task.status['done']
        task.set_status('done', not current_val, propogate=True)
        State['unsaved_command_counter'] += 1

    elif cmd.opcode == 'e':
        State['display_urgent'], State['display_priority'] = False, False
        task.set_expension(not task.expand)

    elif cmd.opcode == 'r':
        task.name = cmd.data
        State['unsaved_command_counter'] += 1

    elif cmd.opcode == 'p':
        task.period = {'activationDay': cmd.data, 'lastActivation': date.today()}
        State['unsaved_command_counter'] += 1

    elif all(chr == 'w' for chr in cmd.opcode) or all(chr == 's' for chr in cmd.opcode):
        direction = 1 if cmd.opcode.startswith('s') else -1
        if State['display_agenda']:
            if task not in State['agenda_order']:
                return
            src = State['agenda_order'].index(task)
            dst = (src + direction * len(cmd.opcode)) % len(State['agenda_order'])
            State['agenda_order'].insert(dst, State['agenda_order'].pop(src))
        else:
            parent_task_list = Tasks if len(cmd.task_location) == 1 else get_task(Tasks, cmd.task_location[:-1]).subTasks
            dst = (cmd.task_location[-1] + direction * len(cmd.opcode)) % len(parent_task_list)
            parent_task_list.insert(dst, parent_task_list.pop(parent_task_list.index(task)))
            State['unsaved_command_counter'] += 1

    elif cmd.opcode == 'rm' or cmd.opcode == 'del':
        pointer = cmd.task_location[-1]
        if len(cmd.task_location) == 1:
            del Tasks[pointer]
        else:
            parent_task = get_task(Tasks, cmd.task_location[:-1])
            del parent_task.subTasks[pointer]
        State['unsaved_command_counter'] += 1

    elif cmd.opcode == 'c':
        color_code = cmd.data if cmd.data in color_dict.keys() else 'w'
        color = color_dict[color_code]
        task.set_color(color)
        State['unsaved_command_counter'] += 1

    elif cmd.opcode == 'const':
        State['constant_parent_task'] = cmd.task_location

    else:
        if not cmd.opcode in opcode_dict:
            task.add_subTask(' '.join([cmd.opcode, cmd.data]))
            State['unsaved_command_counter'] += 1

def save_data_wrapper(State, Tasks):
    save_data(State, Tasks)
    State['unsaved_command_counter'] = 0
    State['previous_saved_time'] = time()

def sparse_data_saver(State, Tasks):
    if State['unsaved_command_counter'] > MAX_UNSAVED_COMMANDS:
        save_data_wrapper(State, Tasks)
        return

    if State['unsaved_command_counter'] > 1 and time() - State['previous_saved_time'] > MAX_UNSAVED_TIME:
        save_data_wrapper(State, Tasks)
        return

def init_state():
    State = initial_state.copy()
    State['agenda_order'] = []
    State['lines_since_last_erase'] = 0
    State['undo_stack'] = []
    State['redo_stack'] = []
    State['unsaved_command_counter'] = 0
    State['previous_saved_time'] = time()
    return State

def main():
    sys_print('welcome to TODO list:')

    _, Tasks = load_data()
    State = init_state()
    update_tasks(Tasks)
    for task in Tasks:
        task.set_expension(False)

    real_stdout = sys.__stdout__ if sys.__stdout__ is not None else sys.stdout
    sys.stdout = LineCountingStream(real_stdout, State)

    display_tasks(State, Tasks)

    while True:
        try:
            raw = input()
            State['lines_since_last_erase'] += 1
            cmd = Command(raw, State)
            cmd.execute(State, Tasks)
            display_tasks(State, Tasks)
            sparse_data_saver(State, Tasks)

        except SystemExit:
            save_data(State, Tasks)
            sys_print('good bye.')
            sys.exit()

        except Exception as e:
            State["display_urgent"] = False
            sys_print(f'error: {e}')


if __name__ == '__main__':
    main()

# pyinstaller --onefile main.py
