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
OUTPUT_ON = True

class TranscriptionClient:
    output_on = False
    tc_main_loop = None
    update_caption_line_channel = None

    def __init__(self, update_caption_line_channel = None, output_on = False):
        self.output_on = output_on
        self.tc_main_loop = None
        self.update_caption_line_channel = update_caption_line_channel

    def update_caption_line(self, caption_line):
        if self.update_caption_line_channel != None:
            self.update_caption_line_channel.emit(caption_line)

    # transcription main
    async def _transcribe_main(self):
        # transcription interface
        transcribe_client = TranscribeStreamingClient(region="us-west-2")
        transcribe_stream = await transcribe_client.start_stream_transcription(
            language_code="en-US",
            media_sample_rate_hz=SAMPLING_RATE,#16000,
            media_encoding="pcm",
        )
        class TranscriptionResultHandler(TranscriptResultStreamHandler):
            def __init__(self, stream, client):
                super().__init__(stream)
                self.client = client
                self.last_transcription = ""
            async def handle_transcript_event(self, transcript_event: TranscriptEvent):
                results = transcript_event.transcript.results
                for result in results:
                    for alt in result.alternatives:
                        if alt.transcript != self.last_transcription:
                            self.last_transcription = alt.transcript
                            if OUTPUT_ON:
                                print(alt.transcript)
                            self.client.update_caption_line(alt.transcript)

        transcription_result_handler = TranscriptionResultHandler(transcribe_stream.output_stream, self)

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
        if OUTPUT_ON:
            print ("listening")
        stream.start_stream()
        await transcription_result_handler.handle_events()
        if OUTPUT_ON:
            print ("done")

        # done
        await transcribe_stream.input_stream.end_stream()
        if ECHO:
            output_stream.stop_stream()
            output_stream.close()
        stream.stop_stream()
        stream.close()
        audio.terminate()

    def transcribe(self):
        # entry point
        self.tc_main_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.tc_main_loop)
        self.tc_main_loop.run_until_complete(self._transcribe_main())
        # self.tc_main_loop.run_forever(self._transcribe_main())
    
    def stop(self):
        self.tc_main_loop.stop()
        # self.tc_main_loop.close()



if __name__=="__main__":
    # tc = new 
    tc = TranscriptionClient(None, OUTPUT_ON)
    tc.transcribe()