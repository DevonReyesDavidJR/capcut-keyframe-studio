"""
Audio Analyzer Module
Detects beats, onsets, and rhythmic pulses from audio files or BPM parameters.
Uses standard Python library (wave, struct, math) + optional ffmpeg for universal format support.
"""

import os
import sys
import wave
import struct
import math
import shutil
import tempfile
import subprocess
from typing import List, Dict, Any, Optional, Tuple

class AudioAnalyzer:
    """Extracts beat timestamps in microseconds from audio files or BPM inputs."""

    @staticmethod
    def is_ffmpeg_available() -> bool:
        """Checks if ffmpeg binary exists in PATH."""
        return shutil.which("ffmpeg") is not None

    @classmethod
    def convert_to_wav(cls, input_audio_path: str, output_wav_path: str, duration_sec: Optional[float] = None) -> bool:
        """Converts any audio/video file to 16kHz mono 16-bit WAV using ffmpeg."""
        if not cls.is_ffmpeg_available():
            return False

        cmd = [
            "ffmpeg", "-y",
            "-i", input_audio_path,
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-f", "wav"
        ]
        if duration_sec:
            cmd.extend(["-t", str(duration_sec)])
        cmd.append(output_wav_path)

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return os.path.exists(output_wav_path)
        except Exception as e:
            return False

    @classmethod
    def detect_beats_from_file(
        cls,
        audio_path: str,
        sensitivity: float = 1.35,      # Multiplier over moving average (1.1 - 2.0)
        min_interval_ms: int = 220,     # Min distance between consecutive beats (avoids machine-gun triggers)
        max_duration_sec: float = 120.0 # Limit analysis to 2 mins for instant response
    ) -> List[int]:
        """
        Analyzes audio signal energy to detect beat/bass onsets.
        Returns list of beat timestamps in microseconds (us).
        """
        if not os.path.exists(audio_path):
            return []

        # If already a 16-bit PCM wav, read directly; otherwise convert via ffmpeg
        temp_wav = None
        target_path = audio_path

        is_wav = audio_path.lower().endswith(".wav")
        if not is_wav or not cls._is_standard_pcm_wav(audio_path):
            if not cls.is_ffmpeg_available():
                # Fallback to simulated BPM if ffmpeg is missing
                return cls.generate_bpm_beats(120.0, int(max_duration_sec * 1_000_000))

            temp_dir = tempfile.gettempdir()
            temp_wav = os.path.join(temp_dir, f"capcut_audio_{os.getpid()}_{hash(audio_path) & 0xfffffff}.wav")
            ok = cls.convert_to_wav(audio_path, temp_wav, duration_sec=max_duration_sec)
            if not ok or not os.path.exists(temp_wav):
                if temp_wav and os.path.exists(temp_wav):
                    os.remove(temp_wav)
                return cls.generate_bpm_beats(120.0, int(max_duration_sec * 1_000_000))
            target_path = temp_wav

        beat_times_us = []
        try:
            with wave.open(target_path, "rb") as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                num_frames = wf.getnframes()

                if sample_width != 2:
                    # Not 16-bit PCM
                    return []

                raw_data = wf.readframes(num_frames)
                total_samples = len(raw_data) // (2 * channels)
                # Unpack short integers (-32768 to 32767)
                fmt = f"<{total_samples * channels}h"
                samples = struct.unpack(fmt, raw_data)

                # If stereo, take channel 0 or average
                if channels > 1:
                    mono_samples = samples[::channels]
                else:
                    mono_samples = samples

                # Window size: ~30ms (e.g. 480 samples at 16kHz)
                window_size = int(framerate * 0.030)
                hop_size = int(framerate * 0.015)  # 15ms hop
                if window_size == 0 or hop_size == 0:
                    return []

                energies = []
                frame_times_us = []

                for i in range(0, len(mono_samples) - window_size, hop_size):
                    window = mono_samples[i : i + window_size]
                    # Calculate Root Mean Square energy
                    energy = math.sqrt(sum(s * s for s in window) / float(window_size))
                    energies.append(energy)
                    time_us = int((i / float(framerate)) * 1_000_000)
                    frame_times_us.append(time_us)

                if not energies:
                    return []

                # Dynamic moving average threshold
                # Window for moving average: ~0.8 seconds (approx 50 hops)
                ma_window = 50
                min_gap_us = min_interval_ms * 1000
                last_beat_us = -min_gap_us

                max_energy = max(energies) if energies else 1.0
                noise_floor = max_energy * 0.12  # Ignore quiet background noise

                for idx in range(len(energies)):
                    cur_energy = energies[idx]
                    if cur_energy < noise_floor:
                        continue

                    # Local average
                    start_idx = max(0, idx - ma_window // 2)
                    end_idx = min(len(energies), idx + ma_window // 2 + 1)
                    local_avg = sum(energies[start_idx:end_idx]) / float(end_idx - start_idx)

                    # Peak check: is it a local peak and higher than sensitivity * local_avg?
                    is_peak = True
                    if idx > 0 and cur_energy < energies[idx - 1]:
                        is_peak = False
                    if idx < len(energies) - 1 and cur_energy < energies[idx + 1]:
                        is_peak = False

                    if is_peak and cur_energy > (local_avg * sensitivity):
                        t_us = frame_times_us[idx]
                        if t_us - last_beat_us >= min_gap_us:
                            beat_times_us.append(t_us)
                            last_beat_us = t_us

        except Exception as e:
            pass
        finally:
            if temp_wav and os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass

        return beat_times_us

    @classmethod
    def _is_standard_pcm_wav(cls, path: str) -> bool:
        try:
            with wave.open(path, "rb") as wf:
                return wf.getsampwidth() == 2 and wf.getcomptype() == "NONE"
        except Exception:
            return False

    @staticmethod
    def generate_bpm_beats(
        bpm: float = 120.0,
        total_duration_us: int = 15_000_000,
        offset_ms: int = 0
    ) -> List[int]:
        """
        Generates mathematically precise beat timestamps based on BPM.
        """
        if bpm <= 0:
            bpm = 120.0

        beat_interval_us = int((60.0 / bpm) * 1_000_000)
        cur_t = offset_ms * 1000
        beats = []

        while cur_t < total_duration_us:
            if cur_t >= 0:
                beats.append(cur_t)
            cur_t += beat_interval_us

        return beats
