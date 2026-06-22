import numpy as np
import pygame
import tempfile
import wave
import threading
import time
from pathlib import Path

_SOUND_CACHE = {}
_BGM_PATH = None
_HOME_BGM_PATH = None
_MIXER_LOCK = threading.Lock()


def _ensure_mixer(init_args=(44100, -16, 2, 2048)):
    """Ensure pygame mixer is initialized robustly."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.pre_init(*init_args)
            pygame.mixer.init()
    except Exception:
        # attempt re-init with safer buffer
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        try:
            pygame.mixer.pre_init(init_args[0], init_args[1], init_args[2], 2048)
            pygame.mixer.init()
        except Exception:
            # last resort: give up silently; callers should guard
            return False
    return True

# Sound Generation
def beep(freq=440, dur=0.1, vol=0.3, rate=44100):
    frames = int(dur * rate)
    t = np.linspace(0, dur, frames, False)
    wave_arr = np.sin(2 * np.pi * freq * t)
    fade = np.linspace(1.0, 0.0, frames)
    wave_arr = wave_arr * fade * vol
    arr = (wave_arr * 32767).astype(np.int16)
    try:
        return pygame.sndarray.make_sound(np.column_stack([arr, arr]))
    except Exception:
        return None


def load_sounds(settings=None):
    """Generate and cache common sound effects. Returns dict of sounds."""
    _ensure_mixer()
    cache = _SOUND_CACHE
    if cache:
        return cache

    sfx = {
        'paddle': beep(480, 0.08, 0.4),
        'wall':   beep(300, 0.06, 0.3),
        'score':  beep(220, 0.35, 0.5),
        'win':    beep(660, 0.6,  0.6),
        'click':  beep(550, 0.05, 0.3),
    }
    # apply volume multipliers if provided
    try:
        mv = 1.0
        if settings:
            mv = float(settings.get('audio', {}).get('master_volume', 1.0))
            sfx_vol = float(settings.get('audio', {}).get('sfx_volume', 0.8))
        else:
            sfx_vol = 0.8
        for k, snd in sfx.items():
            if snd:
                try:
                    snd.set_volume(sfx_vol * mv)
                except Exception:
                    pass
    except Exception:
        pass

    cache.update(sfx)
    return cache


def generate_game_bgm(rate=44100):
    """Generate a temporary WAV file with energetic game melody and return path."""
    global _BGM_PATH
    if _BGM_PATH and Path(_BGM_PATH).exists():
        return _BGM_PATH

    notes = {
        'C4': 261.63, 'D4': 293.66, 'E4': 329.63,
        'F4': 349.23, 'G4': 392.00, 'A4': 440.00,
        'B4': 493.88, 'C5': 523.25, 'G3': 196.00,
        'REST': 0
    }
    melody = [
        ('C4', 0.2), ('E4', 0.2), ('G4', 0.2), ('C5', 0.4),
        ('B4', 0.2), ('G4', 0.2), ('E4', 0.2), ('C4', 0.4),
        ('F4', 0.2), ('A4', 0.2), ('C5', 0.2), ('A4', 0.4),
        ('G4', 0.2), ('E4', 0.2), ('D4', 0.2), ('C4', 0.4),
    ]

    def make_track(sequence):
        track = np.array([], dtype=np.float64)
        for note, dur in sequence:
            frames = int(dur * rate)
            if note == 'REST':
                segment = np.zeros(frames)
            else:
                freq = notes[note]
                t = np.linspace(0, dur, frames, False)
                # use sine wave
                segment = np.sin(2 * np.pi * freq * t)
                # longer attack and release to avoid clicks
                attack  = min(int(0.02 * rate), frames // 3)
                release = min(int(0.08 * rate), frames // 3)
                env = np.ones(frames)
                env[:attack]   = np.linspace(0, 1, attack)
                env[-release:] = np.linspace(1, 0, release)
                segment = segment * env
            # crossfade join — blend last 64 samples with next segment start
            if len(track) > 64 and len(segment) > 64:
                fade_out = np.linspace(1, 0, 64)
                fade_in  = np.linspace(0, 1, 64)
                track[-64:] = track[-64:] * fade_out + segment[:64] * fade_in
                segment = segment[64:]
            track = np.concatenate([track, segment])
        return track

    mel = make_track(melody)
    # normalize to 70% to avoid clipping
    peak = np.max(np.abs(mel))
    if peak > 0:
        mel = mel / peak * 0.70
    mixed_int = (mel * 32767).astype(np.int16)
    stereo = np.column_stack([mixed_int, mixed_int])

    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    with wave.open(tmp.name, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(stereo.tobytes())
    _BGM_PATH = tmp.name
    return _BGM_PATH


def generate_bgm(rate=44100):
    """Backward-compatible alias for generate_game_bgm()."""
    return generate_game_bgm(rate)


def generate_home_bgm(rate=44100):
    """Generate a temporary WAV file with slow ambient home screen melody and return path."""
    global _HOME_BGM_PATH
    if _HOME_BGM_PATH and Path(_HOME_BGM_PATH).exists():
        return _HOME_BGM_PATH

    notes = {
        'C4': 261.63, 'E4': 329.63, 'G4': 392.00, 'A4': 440.00, 'REST': 0
    }
    # Slow, ambient melody for home screen
    melody = [
        ('C4', 0.4), ('E4', 0.4), ('G4', 0.4), ('A4', 0.8),
        ('REST', 0.2), ('A4', 0.4), ('G4', 0.4), ('E4', 0.8),
        ('REST', 0.2), ('C4', 0.4), ('E4', 0.4), ('G4', 0.4), ('C4', 0.8),
    ]

    def make_track(sequence):
        track = np.array([], dtype=np.float64)
        for note, dur in sequence:
            frames = int(dur * rate)
            if note == 'REST':
                segment = np.zeros(frames)
            else:
                freq = notes[note]
                t = np.linspace(0, dur, frames, False)
                segment = np.sin(2 * np.pi * freq * t)
                attack  = min(int(0.04 * rate), frames // 3)
                release = min(int(0.12 * rate), frames // 3)
                env = np.ones(frames)
                env[:attack]   = np.linspace(0, 1, attack)
                env[-release:] = np.linspace(1, 0, release)
                segment = segment * env
            if len(track) > 64 and len(segment) > 64:
                fade_out = np.linspace(1, 0, 64)
                fade_in  = np.linspace(0, 1, 64)
                track[-64:] = track[-64:] * fade_out + segment[:64] * fade_in
                segment = segment[64:]
            track = np.concatenate([track, segment])
        return track

    mel = make_track(melody)
    peak = np.max(np.abs(mel))
    if peak > 0:
        mel = mel / peak * 0.60
    mixed_int = (mel * 32767).astype(np.int16)
    stereo = np.column_stack([mixed_int, mixed_int])

    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    with wave.open(tmp.name, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(stereo.tobytes())
    _HOME_BGM_PATH = tmp.name
    return _HOME_BGM_PATH


def start_bgm(settings=None):
    """Start background music with health checks and volume control."""
    _ensure_mixer()
    try:
        bgm_file = generate_bgm()
        if not bgm_file:
            return None
        with _MIXER_LOCK:
            try:
                pygame.mixer.music.load(bgm_file)
                vol = 0.35
                if settings:
                    vol = float(settings.get('audio', {}).get('bgm_volume', vol))
                    if settings.get('audio', {}).get('mute', False):
                        vol = 0.0
                    vol = vol * float(settings.get('audio', {}).get('master_volume', 1.0))
                pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play(-1)
            except Exception:
                # try re-init and load once
                try:
                    pygame.mixer.quit()
                    _ensure_mixer()
                    pygame.mixer.music.load(bgm_file)
                    pygame.mixer.music.play(-1)
                except Exception:
                    return None

        # start a background health-check thread
        def _health():
            while True:
                time.sleep(10)
                try:
                    if not pygame.mixer.get_init():
                        _ensure_mixer()
                        with _MIXER_LOCK:
                            pygame.mixer.music.load(bgm_file)
                            pygame.mixer.music.play(-1)
                except Exception:
                    pass

        t = threading.Thread(target=_health, daemon=True)
        t.start()
        return bgm_file
    except Exception:
        return None


def stop_bgm():
    try:
        pygame.mixer.music.stop()
    except Exception:
        try:
            pygame.mixer.quit()
        except Exception:
            pass


def start_home_bgm(settings=None):
    """Start home screen background music with health checks and volume control."""
    _ensure_mixer()
    try:
        bgm_file = generate_home_bgm()
        if not bgm_file:
            return None
        with _MIXER_LOCK:
            try:
                pygame.mixer.music.load(bgm_file)
                vol = 0.25
                if settings:
                    vol = float(settings.get('audio', {}).get('bgm_volume', vol))
                    if settings.get('audio', {}).get('mute', False):
                        vol = 0.0
                    vol = vol * float(settings.get('audio', {}).get('master_volume', 1.0))
                pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play(-1)
            except Exception:
                # try re-init and load once
                try:
                    pygame.mixer.quit()
                    _ensure_mixer()
                    pygame.mixer.music.load(bgm_file)
                    pygame.mixer.music.play(-1)
                except Exception:
                    return None

        # start a background health-check thread
        def _health():
            while True:
                time.sleep(10)
                try:
                    if not pygame.mixer.get_init():
                        _ensure_mixer()
                        with _MIXER_LOCK:
                            pygame.mixer.music.load(bgm_file)
                            pygame.mixer.music.play(-1)
                except Exception:
                    pass

        t = threading.Thread(target=_health, daemon=True)
        t.start()
        return bgm_file
    except Exception:
        return None

