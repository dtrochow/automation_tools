#!/usr/bin/env python3
from argparse import ArgumentParser
from subprocess import PIPE, Popen, check_output
import sys
from datetime import datetime
import os


SCRIPT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))

DEFAULT_LOCAL_PORT = 5002
DEFAULT_REMOTE_PORT = 20391
DEFAULT_SSH_PORT = 10391
DEFAULT_REMOTE_USER = "frog"
DEFAULT_REMOTE_SERVER = "frog01.mikr.us"
DEFAULT_LOG_FILE_PATH = os.path.join(SCRIPT_DIR_PATH, "logs", "frog_tunnel.log")

LOG_MAX_LINES_COUNT = 50000


def parse_args(parser):
    parser.add_argument('-lp', '--local_port', dest='local_port', action='store',
                        default=DEFAULT_LOCAL_PORT, help='Destination local port')
    parser.add_argument('-rp', '--remote_port', dest='remote_port', action='store',
                        default=DEFAULT_REMOTE_PORT, help='Remote port, which will be forwarded to local port')
    parser.add_argument('-p', '--ssh_port', dest='ssh_port', action='store',
                        default=DEFAULT_SSH_PORT, help='Port for SSH connection with remote server')
    parser.add_argument('-u', '--remote_user', dest='remote_user', action='store',
                        default=DEFAULT_REMOTE_USER, help='Remote server user')
    parser.add_argument('-r', '--remote_server', dest='remote_server', action='store',
                        default=DEFAULT_REMOTE_SERVER, help='Remote server URL/IP')
    parser.add_argument('-log', '--log_file', dest='log_file', action='store',
                        default=DEFAULT_LOG_FILE_PATH, help='Path for script LOG FILE')
    
    return parser.parse_args()


def log_status(status, log_file_path):
    if not os.path.exists(log_file_path):
        with open(log_file_path, 'w'): pass

    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(status)
    with open(log_file_path, 'r+') as log:
        log_lines = log.readlines()
        if (len(log_lines) >= LOG_MAX_LINES_COUNT):
            log_lines.pop(0)
        log_lines.append(f"{date}: {status}\n")
        log.writelines(log_lines)


def get_alive_tunnels():
    lsof = Popen(['sudo', 'lsof', '-i', '-n'], stdout=PIPE)
    return check_output(('egrep','ssh'), stdin=lsof.stdout, universal_newlines=True).split('\n')


def check_if_tunnel_is_alive(port):
    alive_tunnels = get_alive_tunnels()
    for tunnel in alive_tunnels:
        if ((f":{port}") in tunnel) and ("(ESTABLISHED)" in tunnel):
            return True
    return False


def bring_up_the_tunnel(remote_port, local_port, remote_user, remote_server, ssh_port=None):
    ssh_cmd = ['ssh', '-fN', '-R', f'{remote_port}:localhost:{local_port}', f'{remote_user}@{remote_server}']
    if ssh_port:
        ssh_cmd.insert(2, '-p')
        ssh_cmd.insert(3, f'{ssh_port}')
    ssh_process = Popen(ssh_cmd, stdout=PIPE)
    out, err = ssh_process.communicate()
    print("TUNNEL ESTABLISHED")
    return ssh_process.returncode


if __name__ == "__main__":
    args = parse_args(ArgumentParser(description='Setup SSH-Tunnel'))
    if not check_if_tunnel_is_alive(args.local_port):
        log_status("TUNNEL INACTIVE <!!!>", args.log_file)
        status = bring_up_the_tunnel(args.remote_port, args.local_port, args.remote_user, args.remote_server, ssh_port=args.ssh_port)
        if status != 0:
            print("Something went wrong during establishing the SSH tunnel.")
            sys.exit(-1)
    else:
        log_status("TUNNEL IS ACTIVE", args.log_file)
