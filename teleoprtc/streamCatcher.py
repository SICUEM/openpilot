import asyncio
import uuid
import cv2
import os
import time
import json
from aiortc import RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaRelay
from kafka import KafkaProducer

# Importar las clases del archivo original
from stream import WebRTCOfferStream, StreamingOffer, ConnectionProvider

class VideoTrack(MediaStreamTrack):
    kind = "video"

    def __init__(self, camera_type="driver"):
        super().__init__()
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("No se pudo abrir la cámara")
        self.frame = None
        assert camera_type in ["driver", "wideRoad", "road"], "Invalid camera type"
        self._id = f"{camera_type}:{uuid.uuid4()}"
        self.recv_count = 0

    async def recv(self):
        self.recv_count += 1  # Incrementar el contador
        print(f"recv() llamado {self.recv_count} veces")  # Imprimir cada vez que se llama a recv
        ret, frame = self.cap.read()
        if not ret:
            return None
        self.frame = frame
        return frame

    def stop(self):
        self.cap.release()

async def session_provider(offer):
    # Simular la respuesta remota para la oferta
    offer.sdp = offer.sdp.replace("a=setup:actpass", "a=setup:active")
    answer = RTCSessionDescription(sdp=offer.sdp, type='answer')
    return answer

# Configurar el producer de Kafka
kafka_server = '195.235.211.197:9092'
kafka_topic = 'cameras'

producer = KafkaProducer(
    bootstrap_servers=[kafka_server],
    value_serializer=lambda m: json.dumps(m).encode('utf-8'),
    api_version=(0, 10, 1)  # Especificar la versión API del servidor
)

async def main():
    # Crear la pista de video
    video_track = VideoTrack(camera_type="driver")

    # Crear la instancia de WebRTCOfferStream
    stream = WebRTCOfferStream(
        session_provider=session_provider,
        consumed_camera_types=["driver"],
        consume_audio=False,
        video_producer_tracks=[video_track],
        audio_producer_tracks=[],
        should_add_data_channel=False
    )

    # Iniciar el stream
    try:
        await stream.start()
        print("Stream iniciado correctamente")
    except Exception as e:
        print(f"Error al iniciar el stream: {e}")
        return

    try:
        while True:
            await video_track.recv()
            frame = video_track.frame
            if frame is not None:
                # Codificar la imagen como JPEG
                ret, jpeg = cv2.imencode('.jpg', frame)
                if ret:
                    # Enviar la imagen codificada a Kafka
                    producer.send(kafka_topic, jpeg.tobytes())
                    producer.flush()
            print(f"Total de llamadas a recv(): {video_track.recv_count}")  # Imprimir el total de llamadas a recv
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Captura de imágenes detenida por el usuario.")
    finally:
        await stream.stop()

if __name__ == "__main__":
    asyncio.run(main())
