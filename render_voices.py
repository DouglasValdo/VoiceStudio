"""Render the Biscuit vs. Noir rap battle lines with VoiceStudio's OmniVoice model.

Each character gets one designed voice (OmniVoice voice-design tags). The first
line for each character is rendered in design mode and then used as the clone
reference for every other line, so the voice stays the same across the battle.

Run from a VoiceStudio checkout or environment where `omnivoice` imports:
    python render_voices.py --lines lines.json --out voices
Output: voices/<id>.mp3 (falls back to .wav without ffmpeg) + voices/manifest.json
"""
import argparse, json, os, shutil, subprocess

import torch
import torchaudio

from omnivoice.models.omnivoice import OmniVoice
from omnivoice.utils.dtype import tts_dtype_name

VOICES = {
    "dog":  {"instruct": "male, young adult, low pitch, american accent", "speed": 1.08},
    "cat":  {"instruct": "female, middle-aged, low pitch, british accent", "speed": 1.0},
    "host": {"instruct": "male, elderly, high pitch, australian accent", "speed": 1.12},
}


def best_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", default="lines.json")
    ap.add_argument("--out", default="voices")
    ap.add_argument("--model", default="k2-fsa/OmniVoice")
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    lines = json.load(open(args.lines, encoding="utf-8"))
    os.makedirs(args.out, exist_ok=True)
    device = args.device or best_device()
    model = OmniVoice.from_pretrained(args.model, device_map=device, dtype=getattr(torch, tts_dtype_name(device)))
    sr = model.sampling_rate
    has_ffmpeg = shutil.which("ffmpeg") is not None

    refs = {}  # who -> (wav path, text)
    manifest = {"note": "Voices rendered with VoiceStudio (OmniVoice voice design).", "clips": {}}
    for i, ln in enumerate(lines, 1):
        who, text, cid = ln["who"], ln["text"], ln["id"]
        v = VOICES[who]
        wav_path = os.path.join(args.out, cid + ".wav")
        kw = dict(text=text, language="English", speed=v["speed"])
        if who in refs:
            kw.update(ref_audio=refs[who][0], ref_text=refs[who][1])
        else:
            kw.update(instruct=v["instruct"])
        audio = model.generate(**kw)[0]
        torchaudio.save(wav_path, audio.cpu(), sr)
        if who not in refs:
            refs[who] = (wav_path, text)
        name = cid + ".wav"
        if has_ffmpeg:
            mp3 = os.path.join(args.out, cid + ".mp3")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav_path, "-ac", "1", "-b:a", "96k", mp3], check=True)
            name = cid + ".mp3"
        manifest["clips"][cid] = name
        print(f"[{i}/{len(lines)}] {who}: {text[:60]}", flush=True)

    if has_ffmpeg:  # keep the reference wavs only; mp3s are what the page plays
        ref_paths = {p for p, _ in refs.values()}
        for f in os.listdir(args.out):
            p = os.path.join(args.out, f)
            if f.endswith(".wav") and p not in ref_paths:
                os.remove(p)
    json.dump(manifest, open(os.path.join(args.out, "manifest.json"), "w"), indent=1)
    print("done:", len(manifest["clips"]), "clips in", args.out)


if __name__ == "__main__":
    main()
