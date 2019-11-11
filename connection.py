# -*- coding: utf-8 -*-

import paramiko
import argparse


parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, add_help=False)

parser.add_argument('-h', '--host', dest='host', default='127.0.0.1', type=str, help='Name of the host (e.g. IPv4)')
parser.add_argument('-p', '--port', dest='port', default=22, type=int, help='Port of the host')
parser.add_argument('-gu', '--gmp-username', dest='gmp_user', default='', type=str, help='Username for GMP Service')
parser.add_argument('-gp', '--gmp-password', dest='gmp_pwd', default='', type=str, help='Password for GMP Service')
parser.add_argument('-su', '--ssh-username', dest='ssh_user', default='gmp', type=str, help='Username for SSH')
parser.add_argument('-sp', '--ssh-password', dest='ssh_pwd', default='', type=str, help='Password for SSH')

args = parser.parse_args()

timeout = 5

sock = paramiko.SSHClient()

sock.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sock.connect(hostname=args.host, port=args.port, username=args.ssh_user, password=args.ssh_pwd, timeout=timeout, allow_agent=False, look_for_keys=False)


stdin, stdout, stderr = sock.exec_command('', get_pty=False)

#Connect to GMP Service

auth_xml = '<authenticate><credentials><username>{user}</username><password>{pwd}</password></credentials></authenticate>'.format(user=args.gmp_user, pwd=args.gmp_pwd)

ret = stdout.channel.send(auth_xml)

response = stdin.channel.recv(1500)

print(response)

while(42):
    x = True

        