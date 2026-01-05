import whisper

model = whisper.load_model("small")

result = model.transcribe(
    "audio_teste2.wav",
    language="pt",
    fp16=False
)

print("TRANSCRIÇÃO:")
print(result["text"])
