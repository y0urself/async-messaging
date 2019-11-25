#!/usr/bin/env python3
import pika
import sys
import uuid

##### TASK==PUBLISHER #####

class XMLRpcClient(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        #creating the callback queue
        secret = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = secret.method.queue

        self.channel.basic_consume(queue=self.callback_queue, on_message_callback=self.on_response, auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='gvm_requests',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=str(n))
        while self.response is None:
            self.connection.process_data_events()
        return self.response

client = XMLRpcClient()

print(str(client.call("<get_version/>")))

print(str(client.call("<get_tasks/>")))

# i = 0
# while(i < 42):
#     message = ' '.join(sys.argv[1:]) or "No input given."
#     message += ' {}'.format(i)

#     #channel.basic_publish(exchange='', routing_key='durable_queue', body=message, properties=pika.BasicProperties(delivery_mode=2))
#     channel.basic_publish(exchange='texchange', routing_key='', body=message, properties=pika.BasicProperties(
#             delivery_mode=2,  # make message persistent
#         ))

#     print(" [x] Sent '{}'".format(message))
#     i = i + 1

# connection.close()