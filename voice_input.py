import subprocess

print("🎙️ JARVIS ovozli input testi")
print()
print("Android mikrofon oynasini ochishga urinaman...")

try:
    subprocess.run([
        "am",
        "start",
        "-a",
        "android.speech.action.RECOGNIZE_SPEECH"
    ])

except Exception as e:
    print("❌ Xato:", e)