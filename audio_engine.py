"""
Audio engine using pygame.mixer.
No-ops gracefully when pygame is not installed or audio files are absent.
Drop OGG/WAV files into assets/audio/ to activate each state track.

Expected filenames:
  idle.ogg        — low ambient loop (menu / no active quests)
  questing.ogg    — battle/focus loop (active questing)
  penalty.ogg     — eerie/ticking loop (penalty zone)
  quest_clear.wav — one-shot chime (quest checked off)
  level_up.wav    — one-shot fanfare (level gained)
  combo.wav       — one-shot flourish (all 3 quests cleared)
"""
import os

_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "audio")
_FADE = 600   # cross-fade duration in ms

_BG_CHANNEL    = 0
_CHIME_CHANNEL = 1

_TRACKS = {
    "idle":     "YTDown_YouTube_Succession-Main-Theme-1-HOUR-EXTENDED-Ve_Media_ObT0RaT_woU_009_128k.mp3",
    "questing": "questing.ogg",
    "penalty":  "penalty.ogg",
}
_CHIMES = {
    "clear":   "quest_clear.wav",
    "levelup": "level_up.ogg",
    "combo":   "combo.ogg",
}


class AudioEngine:
    def __init__(self):
        self._ok     = False
        self._state  = ""
        self._vol    = 0.70
        self._muted  = False

        try:
            import pygame.mixer as mx
            mx.pre_init(44_100, -16, 2, 1024)
            mx.init()
            mx.set_num_channels(4)
            self._mx = mx
            self._ok = True
        except Exception:
            pass

    # ── Public API ────────────────────────────────────────────────────────

    @property
    def available(self) -> bool:
        return self._ok

    def set_state(self, state: str) -> None:
        """Switch the looping background track with a cross-fade."""
        if not self._ok or state == self._state:
            return
        self._state = state
        fname = _TRACKS.get(state, "")
        self._crossfade(os.path.join(_DIR, fname) if fname else "")

    def play_chime(self, name: str) -> None:
        """Fire a one-shot sound effect on the chime channel."""
        if not self._ok or self._muted:
            return
        fname = _CHIMES.get(name, "")
        if not fname:
            return
        path = os.path.join(_DIR, fname)
        if not os.path.exists(path):
            return
        try:
            ch = self._mx.Channel(_CHIME_CHANNEL)
            s  = self._mx.Sound(path)
            s.set_volume(self._vol)
            ch.play(s)
        except Exception:
            pass

    def set_volume(self, vol: float) -> None:
        self._vol = max(0.0, min(1.0, vol))
        self._sync_bg_volume()

    def set_muted(self, muted: bool) -> None:
        self._muted = muted
        self._sync_bg_volume()

    def get_volume(self) -> float:
        return self._vol

    def is_muted(self) -> bool:
        return self._muted

    # ── Internal ──────────────────────────────────────────────────────────

    def _crossfade(self, path: str) -> None:
        if not self._ok:
            return
        try:
            ch = self._mx.Channel(_BG_CHANNEL)
            ch.fadeout(_FADE)
            if path and os.path.exists(path):
                s = self._mx.Sound(path)
                s.set_volume(0.0 if self._muted else self._vol)
                ch.play(s, loops=-1, fade_ms=_FADE)
                self._current_sound = s   # prevent GC
        except Exception:
            pass

    def _sync_bg_volume(self) -> None:
        if not self._ok:
            return
        try:
            if hasattr(self, "_current_sound"):
                self._current_sound.set_volume(0.0 if self._muted else self._vol)
        except Exception:
            pass
