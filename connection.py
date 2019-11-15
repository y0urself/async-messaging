# -*- coding: utf-8 -*-

import paramiko
import pika
import argparse

 
class AmqpHelper():
    """
    For the asynchronous pika-messaging over rabbitmq
    """
    def __init__(self):
        self.param = None
        self.conn = None
        self.chan = None

    def channel(self):
        if self.conn:
            print("creating channel")
            self.chan = self.conn.channel(on_open_callback= self.exchange)
        else:
            print("no channel created ...")

    def exchange(self, exchange):
        if self.chan:
            print("declare exchange")
            self.chan.exchange_declare(exchange=exchange, callback=self.queue)

    def queue(self, queue):
        if self.chan:
            print("declare queue")
            self.chan.queue_declare(queue=queue)

    def publish(self):
        if self.chan:
            self.chan.basic_publish('test_', 'lol-plz', 'i_am_a_message_...')
        else:
            print("basically not published")

    def start(self):
        if self.conn and not self.conn.is_open:
            self.conn.ioloop.start()                #now we are lost in the loop ...! maybe thread it out?
        else:
            print("not started")
            

class ConnDummy():
    """
    simplified the gvm-tools connection for this usecase.
    """
    def __init__(self):
        self.parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, add_help=False)
        self.timeout = 5
        self.sock = None
        self.args = None
        self.stdin = None
        self.stdout = None
        self.stderr = None

        self.amqp = None

    def parse(self):
        self.parser.add_argument('-p', '--port', dest='port', default=22, type=int, help='Port of the host')
        self.parser.add_argument('-h', '--host', dest='host', default='127.0.0.1', type=str, help='Name of the host (e.g. IPv4)')
        self.parser.add_argument('-gu', '--gmp-username', dest='gmp_user', default='', type=str, help='Username for GMP Service')
        self.parser.add_argument('-gp', '--gmp-password', dest='gmp_pwd', default='', type=str, help='Password for GMP Service')
        self.parser.add_argument('-su', '--ssh-username', dest='ssh_user', default='gmp', type=str, help='Username for SSH')
        self.parser.add_argument('-sp', '--ssh-password', dest='ssh_pwd', default='', type=str, help='Password for SSH')

        self.args = self.parser.parse_args()

    def connect(self):
        self.sock = paramiko.SSHClient()

        self.sock.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.sock.connect(
                hostname=self.args.host, 
                port=self.args.port, 
                username=self.args.ssh_user, 
                password=self.args.ssh_pwd, 
                timeout=self.timeout, 
                allow_agent=False, 
                look_for_keys=False)
        except Exception as e:
            print("Connecting failed: " + str(e))
            return False

        self.stdin, self.stdout, self.stderr = self.sock.exec_command('', get_pty=False)
        return True

    def authenticate(self):
        #Connect to GMP Service

        auth_xml = '<authenticate><credentials><username>{user}</username><password>{pwd}</password></credentials></authenticate>'.format(user=self.args.gmp_user, pwd=self.args.gmp_pwd)

        ret = self.stdout.channel.send(auth_xml)
        print(ret)

        response = self.stdin.channel.recv(1500)
        valid = '<authenticate_response status="200" status_text="OK">'
        if valid in str(response):
            print('Authentication successful')
            return True
        else:
            print(response)
            return False

    def setup(self):
        self.amqp = AmqpHelper()

        # scheme://username:password@host:port/virtual_host?key=value&key=value
        self.amqp.param = pika.URLParameters('amqp://guest:guest@localhost:5672/%2F')
        self.amqp.conn = pika.SelectConnection(parameters = self.amqp.param, on_open_callback=self.amqp.channel)

def main():
    conn = ConnDummy()
    conn.parse()

    if not conn.connect():
        exit(1)

    if not conn.authenticate():
        exit(1)

    conn.setup()

    #TODO We want to wait for requests here, 
    # that we can pass over to the GMP
    try:
        print("connecting pika pika")
        conn.amqp.start()
    except KeyboardInterrupt:
        print("is this .... " + str(conn.amqp.conn.is_open))
        print("catched ...")
        #conn.amqp.conn.close() # the tut says close but the reality says ConnectionWrongStateError. ^^

        # Start the IOLoop again so Pika can communicate, it will stop on its own when the connection is closed
        #conn.amqp.start()

if __name__ == '__main__':
    main()