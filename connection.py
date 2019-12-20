# -*- coding: utf-8 -*-

import paramiko
import pika
import argparse
            
class GVMSSHConnection():
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

        #self.amqp = None

    def parse(self):
        self.parser.add_argument('-p', '--port', dest='port', default=22, type=int, help='Port of the host')
        self.parser.add_argument('-ho', '--host', dest='host', default='127.0.0.1', type=str, help='Name of the host (e.g. IPv4)')
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
            print("Connecting to GVM failed: " + str(e))
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

    def get(self, request):
        self.stdout.channel.send(request)

        return self.stdin.channel.recv(150000) #TODO whatever size I need here ...

class XMLRpcServer(object):
    def __init__(self, conn):
        self.conn = conn
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue='gvm_requests')

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='gvm_requests', on_message_callback=self.on_request)

    def consume(self):
        #TODO We want to wait for requests here, 
        # that we can pass over to the GVM
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.connection.close()
            return

    def on_request(self, ch, method, props, body):
        print("XML Request '{}' received".format(body.decode("utf-8")))

        response = self.conn.get(body)

        properties = pika.BasicProperties(correlation_id = props.correlation_id)

        ch.basic_publish(exchange='', 
                        routing_key=props.reply_to, 
                        properties=properties,
                        body=response.decode("utf-8")
                        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    conn = GVMSSHConnection()
    conn.parse()

    if not conn.connect():
        exit(1)

    if not conn.authenticate():
        print("Authenticating to GVM failed ...")
        exit(1)

    serv = XMLRpcServer(conn)

    serv.consume()

if __name__ == '__main__':
    main()