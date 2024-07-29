from confluent_kafka import Producer
import bz2
import json

bootstrap_servers = '195.235.211.197:9092'
logs_topic = 'logs-c3'
cameras_topic = 'cameras'

def send_logs():
    data = leer_fichero()
    if data:
        p = Producer({
            'bootstrap.servers': bootstrap_servers,
            'api.version.request': 'true',  # Esto asegura que la versión API sea compatible
        })
        try:
            p.produce(logs_topic, value=json.dumps(data).encode('utf-8'))
            p.flush()
            print("Datos enviados correctamente al topic logs-c3")
        except Exception as e:
            print(f"Error al enviar datos: {e}")
    else:
        print("No se enviaron datos porque el archivo no fue leído correctamente")

def leer_fichero():
    ruta_fichero = 'ftpPrueba.txt.bz2'
    try:
        with bz2.open(ruta_fichero, 'rt') as file:
            return file.read()
    except FileNotFoundError:
        print("El archivo no existe")
        return None
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None

def send_data_to_topic(data, topic):
    if data:
        p = Producer({
            'bootstrap.servers': bootstrap_servers,
            'api.version.request': 'true',  
        })
        try:
            p.produce(topic, value=json.dumps(data).encode('utf-8'))
            p.flush()
            print(f"Datos enviados correctamente al topic {topic}")
        except Exception as e:
            print(f"Error al enviar datos al topic {topic}: {e}")
    else:
        print(f"No se enviaron datos al topic {topic} porque el archivo no fue leído correctamente")

if __name__ == "__main__":
    send_logs()

