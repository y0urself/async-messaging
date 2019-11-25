# -*- coding: utf-8 -*-

import paramiko
import pika
import argparse

 
# class AmqpHelper():
#     """
#     For the asynchronous pika-messaging over rabbitmq
#     """
#     def __init__(self):
#         self.param = None
#         self.conn = None
#         self.chan = None

#     def connect(self, param = pika.URLParameters('amqp://guest:guest@localhost:5672/%2F')):
#         self.param = param
#         self.conn = pika.SelectConnection(parameters = param, on_open_callback=self.channel)

#     def channel(self):
#         if self.conn:
#             print("creating channel")
#             self.chan = self.conn.channel(on_open_callback= self.exchange)
#         else:
#             print("no channel created ...")

#     def exchange(self, exchange):
#         if self.chan:
#             print("declare exchange")
#             self.chan.exchange_declare(exchange=exchange, callback=self.queue)

#     def queue(self, queue):
#         if self.chan:
#             print("declare queue")
#             self.chan.queue_declare(queue=queue)

#     def publish(self):
#         if self.chan:
#             self.chan.basic_publish('test_', 'lol-plz', 'i_am_a_message_...')
#         else:
#             print("basically not published")

#     def start(self):
#         if self.conn and not self.conn.is_open:
#             self.conn.ioloop.start()                #now we are lost in the loop ...! maybe thread it out?
#         else:
#             print("not started")
            

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

        #self.amqp = None

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

    def get(self, request):
        self.stdout.channel.send(request)

        return self.stdin.channel.recv(150000)


conn = ConnDummy()

def on_request(ch, method, props, body):
    print(" Request received {}".format(body))
    #print("Lets open a File ... having a good time ...")
    #with open("lol.txt", 'w') as f:
    #    f.write("lol")
    #print("lol!")
    response = conn.get(body)

    properties = pika.BasicProperties(correlation_id = props.correlation_id)

    ch.basic_publish(exchange='', 
                     routing_key=props.reply_to, 
                     properties=properties,
                     body=str(response)
                     )
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    conn.parse()

    if not conn.connect():
        exit(1)

    if not conn.authenticate():
        exit(1)


    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='gvm_requests')

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='gvm_requests', on_message_callback=on_request)

    #TODO We want to wait for requests here, 
    # that we can pass over to the GMP
    try:
        channel.start_consuming()

        #conn.amqp.start()
    except KeyboardInterrupt:
        connection.close()

if __name__ == '__main__':
    main()