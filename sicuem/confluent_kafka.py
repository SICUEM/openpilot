from confluent_kafka import Producer
import bz2

# Configuración del producer
producer = Producer({
    'bootstrap.servers': '195.235.211.197:9092'
})

def delivery_report(err, msg):
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

def send_logs(file_path):
    with bz2.open(file_path, 'rb') as file:
        for line in file:
            producer.produce('logs_comma', value=line.decode(), on_delivery=delivery_report)
    producer.flush()
