def delivery_callback(err, msg):
    if err:
        print("ERROR: Message failed delivery: {}".format(err))
    else:
        key = msg.key().decode("utf-8")
        value = msg.value().decode("utf-8")
        print(f"Produced event to topic {msg.topic()} \nkey = {key} \nvalue = {value}")


def delivery_report_serialized(err, event):
    if err is not None:
        print(f'Delivery failed on reading for {event.key().decode("utf8")}: {err}')
    else:
        print(
            f'Found a submission:\t {event.key().decode("utf8")} produced to {event.topic()}'
        )
