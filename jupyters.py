#! /usr/bin/env python3

import getpass
import os
import re
import argparse
import libtmux
from tqdm import tqdm

STARTING_PORT = 8888
TOKEN_CONST_PART = 'token_for_user_'
WINDOW_NAME_PREFIX = 'window_'
FOLDER_NAME_PREFIX = 'folder_'
SESSION_NAME_POSTFIX = '_session'


def max_current_folders_number(directory):
    folder_paths = [f.path for f in os.scandir(directory) if f.is_dir()]
    folder_names = re.findall(FOLDER_NAME_PREFIX + '\d+', ''.join(folder_paths))
    folder_numbers = [int(re.search('\d+', name).group(0)) for name in folder_names]
    if len(folder_numbers) > 0:
        return max(folder_numbers)
    else:
        return -1


def start(num_users, base_dir='.', ip='0.0.0.0', ports=None):
    """
    Запустить $num_users ноутбуков. У каждого рабочая директория $base_dir+$folder_num
    """
    if base_dir[-1] != '/':
        base_dir = base_dir + '/'
    if (ports == None):
        ports = list(range(STARTING_PORT, STARTING_PORT + num_users))
    if (len(ports) != num_users):
        raise IndexError("The number of ports must be equal to the number of users")

    server = libtmux.Server()
    session_creator_name = getpass.getuser()

    session_name = session_creator_name + SESSION_NAME_POSTFIX
    if server.has_session(session_name):
        session = server.find_where({"session_name": session_name})
    else:
        session = server.new_session(session_name, start_directory=base_dir)

    next_number_for_folders = max_current_folders_number(base_dir) + 1
    for i in tqdm(range(num_users)):
        current_number = str(next_number_for_folders + i)
        new_dir_path = base_dir + FOLDER_NAME_PREFIX + current_number
        os.mkdir(new_dir_path)
        window = session.new_window(window_name=WINDOW_NAME_PREFIX + current_number,
                                    start_directory=new_dir_path)
        pane = window.attached_pane
        pane.send_keys('jupyter notebook --ip ' + ip + ' --port ' + str(ports[i]) +
                       ' --no-browser --NotebookApp.token=\'' + TOKEN_CONST_PART +
                       current_number + '\' --NotebookApp.notebook_dir=\'./\'')

    pass


def stop(session_name, num):
    """
    @:param session_name: Название tmux-сессии, в которой запущены окружения
    @:param num: номер окружения, кот. можно убить
    """
    server = libtmux.Server()
    if server.has_session(session_name):
        session = server.find_where({"session_name": session_name})
        window_name = WINDOW_NAME_PREFIX + str(num)
        session.kill_window(window_name)
    else:
        raise ValueError("Can't find session: " + session_name)

    pass


def stop_all(session_name):
    """
    @:param session_name: Название tmux-сессии, в которой запущены окружения
    """
    server = libtmux.Server()
    if server.has_session(session_name):
        session = server.find_where({"session_name": session_name})
        session.kill_session()
    else:
        raise ValueError("Can't find session: " + session_name)

    pass


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='command')
subparsers.required = True

parser_start = subparsers.add_parser('start')
parser_start.add_argument('num_users', type=int)
parser_start.add_argument('base_dir', nargs='?', type=str, default='./')
parser_start.add_argument('--ip', '-a', type=str, default='0.0.0.0')
parser_start.add_argument('--ports', '-p', nargs='*', type=int)

parser_stop = subparsers.add_parser('stop')
parser_stop.add_argument('session_name', type=str)
parser_stop.add_argument('num', type=int)

parser_stop_all = subparsers.add_parser('stop_all')
parser_stop_all.add_argument('session_name', type=str)

args = parser.parse_args()

if args.command == 'start':
    start(args.num_users, args.base_dir, args.ip, args.ports)
elif args.command == 'stop':
    stop(args.session_name, args.num)
elif args.command == 'stop_all':
    stop_all(args.session_name)
else:
    pass
