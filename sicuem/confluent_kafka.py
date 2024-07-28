from confluent_kafka import Producer
import bz2
import json

bootstrap_servers = '195.235.211.197:9092'
topic = 'logs-c3'

def send_logs():
    data = leer_fichero()
    if data:
        p = Producer({
            'bootstrap.servers': bootstrap_servers,
            'api.version.request': 'true',  # Esto asegura que la versión API sea compatible
        })
        try:
            p.produce(topic, value=json.dumps(data).encode('utf-8'))
            p.flush()
            print("Datos enviados correctamente")
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

if __name__ == "__main__":
    send_logs()