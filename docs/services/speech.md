# Speech

Speech is a service that enables easy integration of Google speech recognition technologies into developer applications. The `Speech` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Speech-to-Text API.

## Installation

To use the Speech functionality, you need to install gcp-pilot with the speech extra:

```bash title="Install Speech extra"
pip install gcp-pilot[speech]
```

## Usage

### Initialization

```python title="Initialize Speech Client"
from gcp_pilot.speech import Speech

speech = Speech() # (1)!
speech = Speech(project_id="my-project") # (2)!
speech = Speech(impersonate_account="service-account@project-id.iam.gserviceaccount.com") # (3)!
```

1.  Initialize with default credentials
2.  Initialize with specific project
3.  Initialize with service account impersonation

### Converting Speech to Text

#### From Audio Content

```python title="Transcribe Audio Content"
with open("audio.flac", "rb") as audio_file: # (1)!
    audio_content = audio_file.read()
    
transcripts = speech.speech_file_to_text( # (2)!
    flac_content=audio_content,
    language="en-US",  # (3)!
    rate=16000,  # (4)!
    long_running=False,  # (5)!
)

for transcript in transcripts:
    print(f"Transcript: {transcript}")
```

1.  Read audio content from a file
2.  Transcribe the audio content
3.  Optional: defaults to "en"
4.  Optional: sample rate in Hz, defaults to 44100
5.  Optional: if True, uses asynchronous recognition

#### From Audio URI

```python title="Transcribe Audio from GCS URI"
transcripts = speech.speech_uri_to_text( # (1)!
    uri="gs://my-bucket/audio.flac",
    language="en-US",  # (2)!
    rate=16000,  # (3)!
    long_running=False,  # (4)!
)

for transcript in transcripts:
    print(f"Transcript: {transcript}")
```

1.  Convert speech from a GCS URI to text
2.  Optional: defaults to "en"
3.  Optional: sample rate in Hz, defaults to 44100
4.  Optional: if True, uses asynchronous recognition

### Long-Running Recognition

For longer audio files (more than 1 minute), you should use long-running recognition:

```python title="Long-Running Speech Recognition"
transcripts = speech.speech_uri_to_text( # (1)!
    uri="gs://my-bucket/long-audio.flac",
    language="en-US",
    rate=16000,
    long_running=True,  # (2)!
)

for transcript in transcripts:
    print(f"Transcript: {transcript}")
```

1.  Convert speech from a GCS URI to text using long-running recognition
2.  Use asynchronous recognition

## Supported Audio Formats

The Speech API currently supports FLAC format. The audio must be encoded as follows:

- FLAC (Free Lossless Audio Codec) format
- Sample rate hertz matching the actual audio
- Single channel (mono) or 2 channels (stereo)

## Language Support

The Speech API supports a wide range of languages. Some common language codes include:

- `en-US`: English (United States)
- `en-GB`: English (United Kingdom)
- `es-ES`: Spanish (Spain)
- `fr-FR`: French (France)
- `de-DE`: German (Germany)
- `ja-JP`: Japanese (Japan)
- `ru-RU`: Russian (Russia)

For a complete list of supported languages, refer to the [Google Cloud Speech-to-Text documentation](https://cloud.google.com/speech-to-text/docs/languages).

## Error Handling

The Speech class handles common errors and converts them to more specific exceptions:

```python title="Error Handling for Speech API"
from gcp_pilot import exceptions

try:
    transcripts = speech.speech_uri_to_text(uri="gs://non-existent-bucket/audio.flac")
except exceptions.NotFound:
    print("Audio file not found")
except exceptions.InvalidArgument as e:
    print(f"Invalid argument: {e}")
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python title="Using Impersonated Credentials for Speech"
speech = Speech(impersonate_account="service-account@project-id.iam.gserviceaccount.com") # (1)!
transcripts = speech.speech_uri_to_text(uri="gs://my-bucket/audio.flac") # (2)!
```

1.  Initialize with service account impersonation
2.  Now all operations will be performed as the impersonated service account

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

!!! tip "Best Practices for Speech API"
    * **Use the right sample rate**: Ensure the sample rate you specify matches the actual audio sample rate.
    * **Choose the appropriate recognition mode**: Use synchronous recognition for short audio (< 1 minute) and asynchronous recognition for longer audio.
    * **Use GCS URIs for large files**: For large audio files, upload them to Google Cloud Storage and use the URI instead of sending the content directly.
    * **Specify the correct language**: Providing the correct language code improves recognition accuracy.
    * **Consider using enhanced models**: For better accuracy, consider using enhanced models available in the Speech API.
    * **Optimize audio quality**: Better audio quality leads to better recognition results. Reduce background noise and ensure clear speech.
    * **Handle errors gracefully**: Implement proper error handling to manage issues like invalid audio formats or network problems.