#!/usr/bin/env python3
from argparse import ArgumentParser
from subprocess import PIPE, Popen, check_output
import sys
from datetime import datetime
import os

AUTOMATION_TOOLS_DIR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
sys.path.append(AUTOMATION_TOOLS_DIR_PATH)
from signal_bot.signal import SignalCallMeBot


SCRIPT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))

DEFAULT_LOCAL_PORT = 5002
DEFAULT_REMOTE_PORT = 20391
DEFAULT_SSH_PORT = 10391
DEFAULT_REMOTE_USER = "frog"
DEFAULT_REMOTE_SERVER = "frog01.mikr.us"
DEFAULT_LOG_FILE_PATH = os.path.join(SCRIPT_DIR_PATH, "logs", "frog_tunnel.log")

LOG_MAX_LINES_COUNT = 1500


def validate_args(args):
    if ((args.uuid != None) and (args.apikey == None) or
        (args.uuid == None) and (args.apikey != None)):
        raise Exception("--uuid and --apikey can not be specified singly")
    

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
    parser.add_argument('-id', '--uuid', dest='uuid', action='store',
                        default=None, help='UUID of the Signal communicator (it can also be a phone number e.g. +49 123 456 789)')
    parser.add_argument('-k', '--apikey', dest='apikey', action='store',
                        default=None, help='The apikey that you received during the activation process (Signal CallMeBot)')
    
    args = parser.parse_args()
    validate_args(args)

    return args


def clear_log_file(log_file_path):
    os.remove(log_file_path)
    with open(log_file_path, 'w'): pass


def log_status(status, log_file_path):
    print(status)

    if not os.path.exists(log_file_path):
        with open(log_file_path, 'w'): pass

    with open(log_file_path, 'r') as log:
        log_lines = log.readlines()

    clear_log_file(log_file_path)
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file_path, 'w') as log:
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
    try:
        args = parse_args(ArgumentParser(description='Setup SSH-Tunnel'))
    except Exception as e:
        print(e)
        sys.exit(-1)

    if args.uuid:
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        signal = SignalCallMeBot(args.uuid, args.apikey)

    if not check_if_tunnel_is_alive(args.local_port):
        log_status("TUNNEL INACTIVE <!!!>", args.log_file)
        if args.uuid:
            signal.send_message(f"{date}: SSH Tunnel {args.local_port}<->{args.remote_port}:{args.remote_server} <INACTIVE>")
        status = bring_up_the_tunnel(args.remote_port, args.local_port, args.remote_user, args.remote_server, ssh_port=args.ssh_port)
        if status != 0:
            print("Something went wrong during establishing the SSH tunnel.")
            sys.exit(-1)
        if args.uuid:
            signal.send_message(f"{date}: SSH Tunnel {args.local_port}<->{args.remote_port}:{args.remote_server} <ACTIVATED>")
    else:
        log_status("TUNNEL IS ACTIVE", args.log_file)
