# async-messaging
PoC




# Start RabbitMQ

* Start it detached as a daemon - we will be able to monitore it in other ways
    `rabbitmq-server -detached`
* test the server with a ping?

    ```
    >rabbitmqctl ping
    Will ping rabbit@localhost. This only checks if the OS process is running and registered with epmd. Timeout: 60000 ms.
    Ping succeeded
    ```

