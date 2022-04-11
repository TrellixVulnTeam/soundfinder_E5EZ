import asyncio
import pyaudio
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

# constants
NUM_CHANNELS = 1
SAMPLING_RATE = 44100
CHUNK_SIZE = 1024 * 4
AUDIO_FORMAT = pyaudio.paInt16
ECHO = False

# main
async def main():
    # transcription interface
    transcribe_client = TranscribeStreamingClient(region="us-west-2")
    transcribe_stream = await transcribe_client.start_stream_transcription(
        language_code="en-US",
        media_sample_rate_hz=SAMPLING_RATE,#16000,
        media_encoding="pcm",
    )
    class TranscriptionResultHandler(TranscriptResultStreamHandler):
        def __init__(self, stream):
            super().__init__(stream)
            self.last_transcription = ""
        async def handle_transcript_event(self, transcript_event: TranscriptEvent):
            results = transcript_event.transcript.results
            for result in results:
                for alt in result.alternatives:
                    if alt.transcript != self.last_transcription:
                        self.last_transcription = alt.transcript
                        print(alt.transcript)
    transcription_result_handler = TranscriptionResultHandler(transcribe_stream.output_stream)

    # link audio input stream to transcription network stream
    def stream_handler(data, frames, time, status):
        if ECHO:
            output_stream.write(data)
        if transcribe_stream:
            temp_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(temp_loop)
            temp_loop.run_until_complete(transcribe_stream.input_stream.send_audio_event(audio_chunk=data))
        return (None, pyaudio.paContinue)

    # audio interface
    audio = pyaudio.PyAudio()
    stream = audio.open(format=AUDIO_FORMAT, channels=NUM_CHANNELS, rate=SAMPLING_RATE, input=True, frames_per_buffer=CHUNK_SIZE, stream_callback=stream_handler)
    output_stream = None
    if ECHO:
        output_stream = audio.open(format=AUDIO_FORMAT, channels=NUM_CHANNELS, rate=SAMPLING_RATE, output=True, frames_per_buffer=CHUNK_SIZE)

    # listening
    print ("listening")
    stream.start_stream()
    await transcription_result_handler.handle_events()
    print ("done")

    # done
    await transcribe_stream.input_stream.end_stream()
    if ECHO:
        output_stream.stop_stream()
        output_stream.close()
    stream.stop_stream()
    stream.close()
    audio.terminate()

# entry point
main_loop = asyncio.new_event_loop()
asyncio.set_event_loop(main_loop)
main_loop.run_until_complete(main())