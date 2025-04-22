import grpc
from translator.proto import translator_pb2, translator_pb2_grpc
from concurrent.futures import ThreadPoolExecutor
import asyncio

class TranslatorClient:
    def __init__(self, host='localhost', port=50051):
        self.channel = grpc.insecure_channel(f'{host}:{port}')
        self.stub = translator_pb2_grpc.TranslatorStub(self.channel)

    def translate(self, text, source_lang='en', target_lang='ja'):
        request = translator_pb2.TranslateRequest(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang
        )
        response = self.stub.Translate(request)
        return response.translated_text

    def batch_translate(self, texts, source_lang='en', target_lang='ja'):
        request = translator_pb2.BatchTranslateRequest(
            texts=texts,
            source_lang=source_lang,
            target_lang=target_lang
        )
        response = self.stub.BatchTranslate(request)
        return response.translated_texts

    def close(self):
        self.channel.close() 