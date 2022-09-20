from google.cloud.speech_v1 import RecognitionAudio, RecognitionConfig, SpeechClient

from gcp_pilot.base import GoogleCloudPilotAPI


class Speech(GoogleCloudPilotAPI):
    _client_class = SpeechClient

    def speech_file_to_text(self, flac_content, language="en", rate=44100, long_running=False):
        audio = RecognitionAudio(content=flac_content)
        return self._speech_to_text(
            audio=audio,
            language=language,
            rate=rate,
            long_running=long_running,
        )

    def speech_uri_to_text(self, uri, language="en", rate=44100, long_running=False):
        audio = RecognitionAudio(uri=uri)
        return self._speech_to_text(
            audio=audio,
            language=language,
            rate=rate,
            long_running=long_running,
        )

    def _speech_to_text(self, audio, language, rate, long_running=False):
        config = RecognitionConfig(
            encoding=RecognitionConfig.AudioEncoding.FLAC,
            sample_rate_hertz=rate,
            language_code=language,
        )

        if not long_running:
            operation = self.client.recognize(config=config, audio=audio)
            results = operation.results
        else:
            operation = self.client.long_running_recognize(config=config, audio=audio)

            results = operation.result().results

        return [result.alternatives[0].transcript for result in results]


__all__ = ("Speech",)
