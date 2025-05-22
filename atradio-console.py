import pyaudio
import requests
import ffmpeg
import io

# URL радиостанции
radio_url = "http://radio.tatmedia.com:8800/kitapfm"

radio_url="http://retro.volna.top/Retro"

# Настройки аудиопотока
CHUNK = 16384
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

p = pyaudio.PyAudio()

# Открываем поток для воспроизведения
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    output=True
)

# Загружаем поток
response = requests.get(radio_url, stream=True)

# Создаём буфер для ffmpeg
input_stream = io.BytesIO()

# Записываем первые данные в буфер
for block in response.iter_content(CHUNK):
    input_stream.write(block)
    input_stream.seek(0)  # Возвращаемся в начало буфера
    
    # Декодируем с помощью ffmpeg
    try:
        out, _ = (
            ffmpeg
            .input('pipe:0')
            .output('pipe:1', format='s16le', acodec='pcm_s16le', ac=CHANNELS, ar=RATE)
            .run(input=input_stream.read(), capture_stdout=True, capture_stderr=True)
        )
        stream.write(out)
    except ffmpeg.Error as e:
        print("Ошибка декодирования:", e.stderr.decode())
    
    input_stream.seek(0)
    input_stream.truncate()

stream.stop_stream()
stream.close()
p.terminate()




