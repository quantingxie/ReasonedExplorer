# from openai import OpenAI
# import os
# import pyaudio
# import wave
# import audioop
# import subprocess

# class SpeechUtils:
#     def __init__(self, openai_api_key):
#         self.client = OpenAI(api_key=openai_api_key)

#     def speech_to_text(self, audio_file):
#         transcript = self.client.audio.transcriptions.create(
#             model="whisper-1",
#             file=audio_file
#         )
#         return transcript['data']['text']

#     def text_to_speech(self, text, output_file_path):
#         response = self.client.audio.speech.create(
#             model="tts-1",
#             voice="alloy",
#             input=text,
#         )
#         response.stream_to_file(output_file_path)
#         return output_file_path



# def record_until_silence(threshold=500, chunk_size=1024, format=pyaudio.paInt16, channels=1, rate=44100, silence_duration=2):
#     """
#     Records audio from the microphone until silence is detected.
#     :param threshold: The audio level below which is considered silence.
#     :param chunk_size: The chunk size of the audio buffer.
#     :param format: The format of the audio data.
#     :param channels: The number of audio channels.
#     :param rate: The sampling rate.
#     :param silence_duration: The duration of silence (in seconds) to trigger the end of recording.
#     """
#     p = pyaudio.PyAudio()
#     stream = p.open(format=format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk_size)
    
#     print("Recording...")

#     frames = []
#     silence_counter = 0  # Counts silence chunks
#     silence_threshold = silence_duration * rate / chunk_size  # Number of silence chunks to mark end of speech

#     while True:
#         data = stream.read(chunk_size)
#         frames.append(data)

#         # Simple check for audio level below threshold
#         if audioop.rms(data, 2) < threshold:
#             silence_counter += 1
#         else:
#             silence_counter = 0

#         # If we have enough silence, stop recording
#         if silence_counter > silence_threshold:
#             break

#     print("Finished recording.")

#     # Stop and close the stream
#     stream.stop_stream()
#     stream.close()
#     p.terminate()

#     # Save the recorded data as a WAV file
#     wav_filename = "output.wav"
#     wf = wave.open(wav_filename, 'wb')
#     wf.setnchannels(channels)
#     wf.setsampwidth(p.get_sample_size(format))
#     wf.setframerate(rate)
#     wf.writeframes(b''.join(frames))
#     wf.close()

#     # Convert WAV to MP3 using ffmpeg
#     mp3_filename = "audio.mp3"
#     subprocess.run(["ffmpeg", "-i", wav_filename, "-codec:a", "libmp3lame", mp3_filename])

#     return mp3_filename