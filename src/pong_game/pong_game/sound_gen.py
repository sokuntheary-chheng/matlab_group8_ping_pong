import os
import tempfile
import threading
import time
import wave
from pathlib import Path

import numpy as np
import pygame

_SOUND_CACHE = {}
_BGM_PATH = None
_HOME_BGM_PATH = None
_BGM_CHANNEL = None
_BGM_SOUND = None
_MIXER_LOCK = threading.Lock()
_AUDIO_DEBUG = os.environ.get('PONG_AUDIO_DEBUG', '').lower() in ('1', 'true', 'yes')
_LAST_AUDIO_DEBUG_LOG = 0.0
_MIXER_CHANNELS = 32


def _ensure_mixer(init_args=(22050, -16, 2, 4096)):
    """Ensure pygame mixer is initialized robustly."""
    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.pre_init(*init_args)
            pygame.mixer.init()
        pygame.mixer.set_num_channels(_MIXER_CHANNELS)
        pygame.mixer.init() if pygame.mixer.get_init() is None else None
        return True
    except Exception:
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        try:
            pygame.mixer.pre_init(init_args[0], init_args[1], init_args[2], 2048)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(_MIXER_CHANNELS)
            return True
        except Exception:
            return False


def log_mixer_status(force=False):
    """Optionally log mixer and channel state at most once every 10 seconds."""
    global _LAST_AUDIO_DEBUG_LOG
    if not _AUDIO_DEBUG:
        return
    now = time.time()
    if not force and now - _LAST_AUDIO_DEBUG_LOG < 10.0:
        return
    _LAST_AUDIO_DEBUG_LOG = now
    try:
        print(
            '[Audio] mixer=%s channels=%d active=%s music_busy=%s' % (
                pygame.mixer.get_init(),
                pygame.mixer.get_num_channels(),
                pygame.mixer.get_busy(),
                pygame.mixer.music.get_busy()),
            flush=True)
    except Exception as exc:
        print(f'[Audio] mixer diagnostic failed: {exc}', flush=True)

# Sound Generation
def _write_wav_file(data, rate=22050, path=None):
    if path is None:
        tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        path = tmp.name
        tmp.close()
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(data)
    return path


def beep(freq=440, dur=0.1, vol=0.3, rate=22050):
    frames = int(dur * rate)
    t = np.linspace(0, dur, frames, False)
    wave_arr = np.sin(2 * np.pi * freq * t)
    fade = np.linspace(1.0, 0.0, frames)
    wave_arr = wave_arr * fade * vol
    arr = (wave_arr * 32767).astype(np.int16)
    stereo = np.column_stack([arr, arr]).tobytes()
    path = _write_wav_file(stereo, rate=rate)

    try:
        return pygame.mixer.Sound(path)
    except Exception:
        return None


def load_sounds(settings=None):
    """Generate and cache common sound effects. Returns dict of sounds."""
    _ensure_mixer()

    sfx = {
        'paddle': beep(480, 0.08, 0.4),
        'wall':   beep(300, 0.06, 0.3),
        'score':  beep(220, 0.35, 0.5),
        'win':    beep(660, 0.6,  0.6),
        'click':  beep(550, 0.05, 0.3),
    }

    try:
        mv = 1.0
        if settings:
            mv = float(settings.get('audio', {}).get('master_volume', 1.0))
            sfx_vol = float(settings.get('audio', {}).get('sfx_volume', 0.8))
        else:
            sfx_vol = 0.8
        for _, snd in sfx.items():
            if snd:
                try:
                    snd.set_volume(sfx_vol * mv)
                except Exception:
                    pass
    except Exception:
        pass

    _SOUND_CACHE.clear()
    _SOUND_CACHE.update(sfx)
    return _SOUND_CACHE


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


def _play_looping_bgm(path, volume):
    global _BGM_CHANNEL, _BGM_SOUND
    try:
        if _BGM_CHANNEL is None:
            _BGM_CHANNEL = pygame.mixer.Channel(0)
        if _BGM_CHANNEL is not None:
            _BGM_CHANNEL.stop()
            if path:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1)
                _BGM_SOUND = path
    except Exception:
        return None
    return path


def start_bgm(settings=None):
    """Start looping game background music with volume control."""
    _ensure_mixer()
    try:
        bgm_file = generate_bgm()
        if not bgm_file:
            return None
        with _MIXER_LOCK:
            try:
                vol = 0.35
                if settings:
                    vol = float(settings.get('audio', {}).get('bgm_volume', vol))
                    if settings.get('audio', {}).get('mute', False):
                        vol = 0.0
                    vol = vol * float(settings.get('audio', {}).get('master_volume', 1.0))
                _play_looping_bgm(bgm_file, vol)
            except Exception:
                # try re-init and load once
                try:
                    pygame.mixer.quit()
                    _ensure_mixer()
                    _play_looping_bgm(bgm_file, 0.35)
                except Exception:
                    return None

        log_mixer_status(force=True)
        return bgm_file
    except Exception:
        return None


def stop_bgm():
    try:
        with _MIXER_LOCK:
            if _BGM_CHANNEL is not None:
                _BGM_CHANNEL.stop()
            global _BGM_SOUND
            _BGM_SOUND = None
        log_mixer_status(force=True)
    except Exception:
        try:
            pygame.mixer.quit()
        except Exception:
            pass


def start_home_bgm(settings=None):
    """Start looping home screen background music with volume control."""
    _ensure_mixer()
    try:
        bgm_file = generate_home_bgm()
        if not bgm_file:
            return None
        with _MIXER_LOCK:
            try:
                vol = 0.25
                if settings:
                    vol = float(settings.get('audio', {}).get('bgm_volume', vol))
                    if settings.get('audio', {}).get('mute', False):
                        vol = 0.0
                    vol = vol * float(settings.get('audio', {}).get('master_volume', 1.0))
                _play_looping_bgm(bgm_file, vol)
            except Exception:
                # try re-init and load once
                try:
                    pygame.mixer.quit()
                    _ensure_mixer()
                    _play_looping_bgm(bgm_file, 0.25)
                except Exception:
                    return None

        log_mixer_status(force=True)
        return bgm_file
    except Exception:
        return None

