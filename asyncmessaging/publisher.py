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

    def call(self, xml_request):
        """
        Make a XML request to the GVM by this method, just call it with a XML request as a parameter
        """
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='gvm_requests',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=str(xml_request))
        while self.response is None:
            self.connection.process_data_events()
        return self.response.decode("utf-8")

    def __del__(self):
        self.connection.close()

def main():
    client = XMLRpcClient()

    #print(str(client.call("<get_version/>")))
    #print(str(client.call("<get_tasks/>")))
    #print("Received answer: {}".format(client.call("<get_targets/>")))
    #print(client.call('<modify_target target_id="03426c9e-b1f2-4caf-82a5-1a06784ec992"><name>Upstairs Lab</name><hosts>Testtest</hosts></modify_target>'))

    print("Received answer: {}".format(client.call(sys.argv[1])))

if __name__ == '__main__':
    main()