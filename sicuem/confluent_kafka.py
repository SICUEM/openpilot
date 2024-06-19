from confluent_kafka import Producer
import bz2

bootstrap_servers = '195.235.211.197:9092'
topic = 'logs_comma'

def send_logs(data):
    data = leer_fichero()
    p = Producer({'bootstrap.servers': bootstrap_servers})
    p.produce(topic, data)
    p.flush()

def leer_fichero():
    ruta_ficherp = 'ftpPrueba.txt.bz2'
    try:
        with open(ruta_fichero, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print("El archivo no existe")
        return None
