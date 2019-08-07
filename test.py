#coding=utf8
import argparse

import grpc

import yandex.cloud.ai.stt.v2.stt_service_pb2 as stt_service_pb2
import yandex.cloud.ai.stt.v2.stt_service_pb2_grpc as stt_service_pb2_grpc


CHUNK_SIZE = 16000

def gen(folder_id, audio_file_name):
    # Задать настройки распознавания.
    specification = stt_service_pb2.RecognitionSpec(
        language_code='ru-RU',
        profanity_filter=True,
        model='general',
        partial_results=True,
        audio_encoding='LINEAR16_PCM',
        sample_rate_hertz=8000
    )
    streaming_config = stt_service_pb2.RecognitionConfig(specification=specification, folder_id=folder_id)

    # Отправить сообщение с настройками распознавания.
    yield stt_service_pb2.StreamingRecognitionRequest(config=streaming_config)

    # Прочитать аудиофайл и отправить его содержимое порциями.
    with open(audio_file_name, 'rb') as f:
        data = f.read(CHUNK_SIZE)
        while data != b'':
            yield stt_service_pb2.StreamingRecognitionRequest(audio_content=data)
            data = f.read(CHUNK_SIZE)


def run(folder_id, iam_token, audio_file_name):
    # Установить соединение с сервером.
    cred = grpc.ssl_channel_credentials()
    channel = grpc.secure_channel('stt.api.cloud.yandex.net:443', cred)
    stub = stt_service_pb2_grpc.SttServiceStub(channel)

    # Отправить данные для распознавания.
    it = stub.StreamingRecognize(gen(folder_id, audio_file_name), metadata=(('authorization', 'Bearer %s' % iam_token),))

    # Обработать ответы сервера и вывести результат в консоль.
    try:
        for r in it:
            try:
                print('Start chunk: ')
                for alternative in r.chunks[0].alternatives:
                    print('alternative: ', alternative.text)
                print('Is final: ', r.chunks[0].final)
                print('')
            except LookupError:
                print('Not available chunks')
    except grpc._channel._Rendezvous as err:
        print('Error code %s, message: %s' % (err._state.code, err._state.details))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser.add_argument('--token', required=True, help='IAM token')
    # parser.add_argument('--folder_id', required=True, help='folder ID')
    # parser.add_argument('--path', required=True, help='audio file path')
    args = parser.parse_args()
    # yc iam create-token
    args.folder_id = 'b1grnrnn65bd2fr58miv'
    args.token = 'CggVAgAAABoBMRKABDbDjddphWj2MRei83yDcIiiBD6wsIkDLSg_gIA4iXHjXkf8dXbFE4vzn8zJBm1WXD_Qh8pVgGklI6MH7iHEGhPv2pFJiVOl94YVYgwFfe_-Sd78np7bG1N6z4BmWk7h31aCmbMBwCK_7l9kZvvvIqhMALjnC4xPSFkYXu_6NYsjF1XbUA_cleWb4O_3QhNnAn5_tHhCe3t0c3lcFkRvpTV1dkfw6ZqKBLHb5Sw6jvUIfwYvlej1NRDuAHMc-07Wf8pa_w88T2iH3R08svnHrjYhon26DUft7608uFdRp1hhtwDJb2oL9jZl4TkLhxAGpd6c9BjxfPM-u1kwrhi-fMWeYxsDSL2k-_X3GnXyAAm-7AicxZlT4qfwfb_dS5A9dKZu1SQaKL2cv2NrgtqYytEw-_boPFlGEG4Lw6WTELkAWEhDH6bAKraqnWyBAgL3d6s5D10dP-JWjpq6d8uOKXe51_ooQVrK07VH98TtiQABvY6mtUkNfLpcXfoCHrsA046VDrt682pY7FSSSp4-WPZpITz1elHTaNmXTkcsrY0IM3-tJC9o9PdRrXDicKtE5LNdLW6KwE3BBp6cltMiqObMUVYIGjtMWQF5etEf3DhD4rX6MVHt0cHaKYW5P6-J2ELElRafah2GFRQpNGl3I_B4cQD2g4k0pTqOHstchBxhGnIKIDIzZDdkZDc3MDJhYTQyNmNiNzUxMjE1ZDcwZTJlMDZiEO3lqeoFGK23rOoFIjoKFGFqZXFkYjllaXZtdGdtYmI1bHV1EgpzcGVlY2gtc3J2KhRiMWdybnJubjY1YmQyZnI1OG1pdjACMAU4AVABWgA'
    args.path = 'speech.pcm'
    run(args.folder_id, args.token, args.path)