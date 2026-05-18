import numpy as np
import pygame
import tempfile
import wave

def beep(freq=440, dur=0.1, vol=0.3, rate=44100):
    frames = int(dur * rate)
    t = np.linspace(0, dur, frames, False)
    wave_arr = np.sin(2 * np.pi * freq * t)
    fade = np.linspace(1.0, 0.0, frames)
    wave_arr = wave_arr * fade * vol
    arr = (wave_arr * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.column_stack([arr, arr]))

def load_sounds():
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    return {
        'paddle': beep(480, 0.08, 0.4),
        'wall':   beep(300, 0.06, 0.3),
        'score':  beep(220, 0.35, 0.5),
        'win':    beep(660, 0.6,  0.6),
        'click':  beep(550, 0.05, 0.3),
    }

def generate_bgm(rate=44100):
    notes = {
        'C4': 261.63, 'D4': 293.66, 'E4': 329.63,
        'F4': 349.23, 'G4': 392.00, 'A4': 440.00,
        'B4': 493.88, 'C5': 523.25, 'G3': 196.00,
        'REST': 0
    }
    melody = [
        ('C4',0.2),('E4',0.2),('G4',0.2),('C5',0.4),
        ('B4',0.2),('G4',0.2),('E4',0.2),('C4',0.4),
        ('F4',0.2),('A4',0.2),('C5',0.2),('A4',0.4),
        ('G4',0.2),('E4',0.2),('D4',0.2),('C4',0.4),
        ('G3',0.2),('C4',0.2),('E4',0.2),('G4',0.4),
        ('A4',0.2),('G4',0.2),('E4',0.2),('C4',0.4),
        ('D4',0.2),('F4',0.2),('A4',0.2),('C5',0.4),
        ('G4',0.2),('E4',0.2),('C4',0.2),('REST',0.4),
    ]
    bass = [
        ('C4',0.8),('G3',0.8),
        ('F4',0.8),('G3',0.8),
        ('G3',0.8),('C4',0.8),
        ('D4',0.8),('REST',0.8),
    ]

    def make_track(sequence, octave_shift=0, wave_type='sine'):
        track = np.array([], dtype=np.float64)
        for note, dur in sequence:
            frames = int(dur * rate)
            if note == 'REST':
                segment = np.zeros(frames)
            else:
                freq = notes[note] / (2 ** octave_shift)
                t = np.linspace(0, dur, frames, False)
                if wave_type == 'sine':
                    segment = np.sin(2 * np.pi * freq * t)
                else:
                    segment = np.sign(np.sin(2 * np.pi * freq * t)) * 0.5
                attack  = min(int(0.01 * rate), frames)
                release = min(int(0.05 * rate), frames)
                env = np.ones(frames)
                env[:attack]   = np.linspace(0, 1, attack)
                env[-release:] = np.linspace(1, 0, release)
                segment = segment * env
            track = np.concatenate([track, segment])
        return track

    mel  = make_track(melody, 0, 'sine')
    bas  = make_track(bass,   1, 'square')
    mlen = max(len(mel), len(bas))
    mel  = np.tile(mel, int(np.ceil(mlen/len(mel))))[:mlen]
    bas  = np.tile(bas, int(np.ceil(mlen/len(bas))))[:mlen]

    mixed     = np.clip(mel * 0.4 + bas * 0.2, -1.0, 1.0)
    mixed_int = (mixed * 32767 * 0.5).astype(np.int16)
    stereo    = np.column_stack([mixed_int, mixed_int])

    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    with wave.open(tmp.name, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(stereo.tobytes())
    return tmp.name

def start_bgm(volume=0.35):
    bgm_file = generate_bgm()
    pygame.mixer.music.load(bgm_file)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(-1)
    return bgm_file

def stop_bgm():
    pygame.mixer.music.stop()
