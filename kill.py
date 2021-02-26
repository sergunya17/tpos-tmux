#! /usr/bin/env python3

import os

os.system("find . -type d -name 'folder_*' -prune -exec rm -rf {} \;")
os.system("tmux kill-server")

