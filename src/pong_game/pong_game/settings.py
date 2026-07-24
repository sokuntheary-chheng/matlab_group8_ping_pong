import json
import os

DEFAULTS = {
    "gameplay": {
        "ball_start_speed": 4.0,
        "ball_speed_increase_pct": 5.0,
        "paddle_speed_auto": True,
        "paddle_speed_manual": 6.0,
        "winning_score": 5,
        "difficulty": "Normal"
    },
    "audio": {
        "master_volume": 0.8,
        "bgm_volume": 0.4,
        "sfx_volume": 0.7,
        "mute": False
    },
    "display": {
        "fullscreen": False,
        "resolution": "1280x720",
        "show_fps": False,
        "effects": True,
        "court": True
    },
    "controls": {
        "p1_up": "w",
        "p1_down": "s",
        "p2_up": "up",
        "p2_down": "down"
    },
    "accessibility": {
        "colorblind": False,
        "large_text": False,
        "high_contrast": False
    }
}


def settings_path():
    return os.path.expanduser('~/.pong_settings.json')


def get_winning_score(settings_dict, fallback=5):
    gameplay = settings_dict.get('gameplay', {}) if isinstance(settings_dict, dict) else {}
    if not isinstance(gameplay, dict):
        return int(fallback)
    try:
        return int(gameplay.get('winning_score', fallback))
    except (TypeError, ValueError):
        return int(fallback)


def load_settings():
    path = settings_path()
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # deep merge defaults
                merged = {k: v.copy() if isinstance(v, dict) else v for k, v in DEFAULTS.items()}
                for key, val in data.items():
                    if key in merged and isinstance(merged[key], dict) and isinstance(val, dict):
                        merged[key].update(val)
                    else:
                        merged[key] = val
                return merged
    except Exception:
        pass
    return {k: v.copy() if isinstance(v, dict) else v for k, v in DEFAULTS.items()}


def save_settings(data):
    path = settings_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False
