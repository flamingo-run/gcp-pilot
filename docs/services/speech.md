# Speech

Speech is a service that enables easy integration of Google speech recognition technologies into developer applications. The `Speech` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Speech-to-Text API.

## Installation

To use the Speech functionality, you need to install gcp-pilot with the speech extra:

```bash
pip install gcp-pilot[speech]
```

## Usage

### Initialization

```python
from gcp_pilot.speech import Speech

# Initialize with default credentials
speech = Speech()

# Initialize with specific project
speech = Speech(project_id="my-project")

# Initialize with service account impersonation
speech = Speech(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Converting Speech to Text

#### From Audio Content

```python
# Convert speech from audio content to text
with open("audio.flac", "rb") as audio_file:
    audio_content = audio_file.read()
    
transcripts = speech.speech_file_to_text(
    flac_content=audio_content,
    language="en-US",  # Optional: defaults to "en"
    rate=16000,  # Optional: sample rate in Hz, defaults to 44100
    long_running=False,  # Optional: if True, uses asynchronous recognition
)

for transcript in transcripts:
    print(f"Transcript: {transcript}")
```

#### From Audio URI

```python
# Convert speech from a GCS URI to text
transcripts = speech.speech_uri_to_text(
    uri="gs://my-bucket/audio.flac",
    language="en-US",  # Optional: defaults to "en"
    rate=16000,  # Optional: sample rate in Hz, defaults to 44100
    long_running=False,  # Optional: if True, uses asynchronous recognition
)

for transcript in transcripts:
    print(f"Transcript: {transcript}")
```

### Long-Running Recognition

For longer audio files (more than 1 minute), you should use long-running recognition:

```python
# Convert speech from a GCS URI to text using long-running recognition
transcripts = speech.speech_uri_to_text(
    uri="gs://my-bucket/long-audio.flac",
    language="en-US",
    rate=16000,
    long_running=True,  # Use asynchronous recognition
)

for transcript in transcripts:
    print(f"Transcript: {transcript}")
```

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

```python
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

```python
# Initialize with service account impersonation
speech = Speech(impersonate_account="service-account@project-id.iam.gserviceaccount.com")

# Now all operations will be performed as the impersonated service account
transcripts = speech.speech_uri_to_text(uri="gs://my-bucket/audio.flac")
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Best Practices

Here are some best practices for working with the Speech API:

1. **Use the right sample rate**: Ensure the sample rate you specify matches the actual audio sample rate.
2. **Choose the appropriate recognition mode**: Use synchronous recognition for short audio (< 1 minute) and asynchronous recognition for longer audio.
3. **Use GCS URIs for large files**: For large audio files, upload them to Google Cloud Storage and use the URI instead of sending the content directly.
4. **Specify the correct language**: Providing the correct language code improves recognition accuracy.
5. **Consider using enhanced models**: For better accuracy, consider using enhanced models available in the Speech API.
6. **Optimize audio quality**: Better audio quality leads to better recognition results. Reduce background noise and ensure clear speech.
7. **Handle errors gracefully**: Implement proper error handling to manage issues like invalid audio formats or network problems.