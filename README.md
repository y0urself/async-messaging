# async-messaging
PoC


## Requirements

* Running GVM instance, you can connect to
* A GMP Username/Password to authenticate with the GVM over SSH
* Python >3.5

## Start RabbitMQ

* Start it detached as a daemon - we will be able to monitore it in other ways
    `rabbitmq-server -detached`
* test the server with a ping?

```
>rabbitmqctl ping
Will ping rabbit@localhost. This only checks if the OS process is running and registered with epmd. Timeout: 60000 ms.
Ping succeeded
```

## Send XML-Requests

* Start the `XML_server.py`

```python3
python3 XML_server.py --host GVMHostname --gmp-username [username] --gmp-password [password]
```

* Start the `XML_client.py` with a XML-Request as a first argument

Example:
```python3
python3 publisher.py '<get_targets/>'
```
