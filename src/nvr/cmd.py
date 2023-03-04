'''
nvr: helper utils for nvim remote feature
'''
import os
import sys

import argparse
import datetime
import logging
import pathlib
import queue
import re
import subprocess

from multiprocessing import Process, JoinableQueue, Queue, Value, freeze_support, set_start_method


def parse_arguments():
  '''
  parse command line arguments
  '''
  parser = argparse.ArgumentParser(prog='nvr')
  parser.add_argument('--version', action='version', version='%(prog)s 1.0')

  parser.add_argument("-d",
                      "--debug",
                      help="print debug information",
                      action="count",
                      default=0)
  parser.add_argument(
      "--server-name",
      help=
      "remote server name to connect to, if not specified, NVIM_LISTEN_ADDRESS env will be used",
      type=str,
      required=False,
      default=None)
  parser.add_argument("--no-start",
                      help="do not start new instance if no server found",
                      action="store_true",
                      default=False)
  parser.add_argument(
      "--editor",
      help="editor to use when start new instance, default use nvim",
      required=False,
      type=str,
      default='nvim')
  parser.add_argument("addition_args",
                      type=str,
                      metavar="<file>",
                      nargs="*",
                      help="file list to open")

  return parser.parse_args()


def get_server_name(args):
  if args.server_name:
    return args.server_name

  try:
    return os.environ['NVIM_LISTEN_ADDRESS']
  except KeyError:
    logging.error('unable find server name')
    sys.exit(1)


def find_server(server_name):
  cmd_line = ['nvim', '--server', server_name, '--remote-expr', 'version']

  try:
    proc = subprocess.run(cmd_line, check=True, capture_output=True)
    logging.debug('remote version:%s' % proc.stdout)
  except subprocess.CalledProcessError:
    return False
  return True


def get_editor_cmdline(editor):
  return editor.split(' ')


def norm_addition_args(addition_args):
  return map(
      lambda x: x
      if x.startswith('+') else pathlib.Path(x).resolve().as_posix(),
      addition_args)


def main():
  args = parse_arguments()

  if args.debug > 0:
    logging.getLogger('').setLevel(logging.DEBUG)
  else:
    logging.getLogger('').setLevel(logging.INFO)

  server_name = get_server_name(args)

  start_server = False

  if not find_server(server_name):
    if args.no_start:
      logging.error('unable to locate server %s' % server_name)
      sys.exit(2)

    start_server = True

  cmd_line = get_editor_cmdline(args.editor) if start_server else ['nvim']

  cmd_line.append('--listen' if start_server else '--server')
  cmd_line.append(server_name)

  if not start_server:
    cmd_line.append('--remote')

  cmd_line.extend(norm_addition_args(args.addition_args))

  logging.debug('running cmd line:%s' % cmd_line)
  subprocess.run(cmd_line, check=True, shell=False)

if __name__ == '__main__':
  main()
