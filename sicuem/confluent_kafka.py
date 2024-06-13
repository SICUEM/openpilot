from confluent_kafka import Producer
import bz2

bootstrap_servers = '195.235.211.197:9092'
topic = 'logs_comma'

def send_logs(data):
    p = Producer({'bootstrap.servers': bootstrap_servers})
    p.produce(topic, data)
    p.flush()
