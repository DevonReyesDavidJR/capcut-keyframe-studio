"""
Keyframe Engine Module
Generates, transforms, and optimizes CapCut keyframes for video/audio segments.
"""

import uuid
import math
import random
from typing import List, Dict, Any, Optional, Tuple

class KeyframeEngine:
    """Core logic to construct and manipulate CapCut common_keyframes."""

    @staticmethod
    def generate_uuid() -> str:
        """Returns standard uppercase UUID4 matching CapCut formatting."""
        return str(uuid.uuid4()).upper()

    @classmethod
    def create_single_keyframe(
        cls,
        time_offset_us: int,
        value: float,
        curve_type: str = "Line",
        left_control: Optional[Dict[str, float]] = None,
        right_control: Optional[Dict[str, float]] = None,
        graph_id: str = ""
    ) -> Dict[str, Any]:
        """Creates an individual keyframe point dictionary."""
        return {
            "id": cls.generate_uuid(),
            "curveType": curve_type,
            "time_offset": int(max(0, time_offset_us)),
            "left_control": left_control or {"x": 0.0, "y": 0.0},
            "right_control": right_control or {"x": 0.0, "y": 0.0},
            "values": [float(value)],
            "string_value": "",
            "graphID": graph_id
        }

    @classmethod
    def create_property_group(
        cls,
        property_type: str,
        keyframe_list: List[Dict[str, Any]],
        material_id: str = ""
    ) -> Dict[str, Any]:
        """Wraps a list of keyframe points into a CapCut property keyframe group."""
        return {
            "id": cls.generate_uuid(),
            "material_id": material_id,
            "property_type": property_type,
            "keyframe_list": keyframe_list
        }

    # ==========================================
    # RHYTHMIC SWITCH PRESETS (Dành cho clip switch 1s, 2s, 0.8s, Halloween & Garment edit)
    # ==========================================

    @classmethod
    def preset_rhythmic_switch_entrance(
        cls,
        duration_us: int,
        direction: str = "up",          # "up" (dưới vút lên), "down" (trên vút xuống), "left", "right"
        target_pos: float = -0.50,      # Vị trí dừng hiển thị trên màn hình
        offscreen_pos: float = -1.60,   # Vị trí ngoài màn hình
        transition_duration_ms: int = 250, # Thời gian vút vào (ms)
        overshoot: float = 0.08,        # Độ nảy đàn hồi (overshoot)
        fps: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Chuỗi keyframe vút vào mượt mà với độ nảy đàn hồi chuẩn xác (như clip switch - Halloween edit final1).
        """
        prop = "KFTypePositionY" if direction in ["up", "down"] else "KFTypePositionX"
        trans_us = min(duration_us, transition_duration_ms * 1000)
        settle_us = int(trans_us * 0.4)
        peak_us = trans_us - settle_us

        # Tính toán hướng và điểm overshoot
        start_val = offscreen_pos if direction in ["up", "right"] else -offscreen_pos
        # Peak overshoot: nảy lố qua vị trí target một chút rồi nhún lại
        if direction in ["up", "right"]:
            peak_val = target_pos + overshoot
        else:
            peak_val = target_pos - overshoot

        frame_step_us = int(1_000_000 / fps)
        kfs = []

        # Tạo chuỗi keyframe frame-by-frame trong giai đoạn vút để đạt độ mượt tuyệt đối (chuẩn CapCut Desktop)
        cur_t = 0
        while cur_t <= trans_us:
            if cur_t <= peak_us:
                # Giai đoạn vút nhanh vào (Ease-out cubic)
                progress = cur_t / float(peak_us) if peak_us > 0 else 1.0
                eased = 1.0 - math.pow(1.0 - progress, 3)
                val = start_val + (peak_val - start_val) * eased
            else:
                # Giai đoạn nhún nhẹ về vị trí target (Ease-in-out)
                sub_prog = (cur_t - peak_us) / float(settle_us) if settle_us > 0 else 1.0
                eased = 0.5 * (1.0 - math.cos(sub_prog * math.pi))
                val = peak_val + (target_pos - peak_val) * eased

            kfs.append(cls.create_single_keyframe(cur_t, round(val, 4), curve_type="Line"))
            cur_t += frame_step_us

        # Đảm bảo điểm kết thúc giai đoạn vút đạt chuẩn target_pos
        if not kfs or kfs[-1]["time_offset"] != trans_us:
            kfs.append(cls.create_single_keyframe(trans_us, target_pos, curve_type="Line"))

        # Giữ nguyên target_pos cho đến hết thời lượng của clip
        if trans_us < duration_us:
            kfs.append(cls.create_single_keyframe(duration_us, target_pos, curve_type="Line"))

        # Đi kèm giữ nguyên trục còn lại ở 0.0 và xoay ở 0.0
        other_prop = "KFTypePositionX" if prop == "KFTypePositionY" else "KFTypePositionY"
        other_kfs = [
            cls.create_single_keyframe(0, 0.0, curve_type="Line"),
            cls.create_single_keyframe(duration_us, 0.0, curve_type="Line")
        ]
        rot_kfs = [
            cls.create_single_keyframe(0, 0.0, curve_type="Line"),
            cls.create_single_keyframe(duration_us, 0.0, curve_type="Line")
        ]

        return [
            cls.create_property_group(prop, kfs),
            cls.create_property_group(other_prop, other_kfs),
            cls.create_property_group("KFTypeRotation", rot_kfs)
        ]

    @classmethod
    def preset_rhythmic_switch_exit(
        cls,
        duration_us: int,
        direction: str = "down",         # "down" (vút xuống), "up", "left", "right"
        current_pos: float = -0.50,     # Vị trí đang đứng
        offscreen_pos: float = -1.60,   # Vị trí rời khỏi màn hình
        transition_duration_ms: int = 200, # Thời gian vút ra ở cuối clip (ms)
        fps: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Chuỗi keyframe vút ra khỏi màn hình ở cuối clip (như Track 4 trong Halloween edit).
        """
        prop = "KFTypePositionY" if direction in ["up", "down"] else "KFTypePositionX"
        trans_us = min(duration_us, transition_duration_ms * 1000)
        start_trans_t = max(0, duration_us - trans_us)
        end_val = offscreen_pos if direction in ["down", "left"] else -offscreen_pos

        frame_step_us = int(1_000_000 / fps)
        kfs = []

        # Giữ nguyên vị trí ban đầu đến khi bắt đầu transition
        kfs.append(cls.create_single_keyframe(0, current_pos, curve_type="Line"))
        if start_trans_t > 0:
            kfs.append(cls.create_single_keyframe(start_trans_t, current_pos, curve_type="Line"))

        # Giai đoạn vút ra với gia tốc nhanh dần (Ease-in quadratic/cubic)
        cur_t = start_trans_t
        while cur_t <= duration_us:
            progress = (cur_t - start_trans_t) / float(trans_us) if trans_us > 0 else 1.0
            eased = math.pow(progress, 2.5)  # Lao nhanh dần ra khỏi màn hình
            val = current_pos + (end_val - current_pos) * eased
            kfs.append(cls.create_single_keyframe(cur_t, round(val, 4), curve_type="Line"))
            cur_t += frame_step_us

        if kfs[-1]["time_offset"] < duration_us:
            kfs.append(cls.create_single_keyframe(duration_us, end_val, curve_type="Line"))

        other_prop = "KFTypePositionX" if prop == "KFTypePositionY" else "KFTypePositionY"
        other_kfs = [
            cls.create_single_keyframe(0, 0.0, curve_type="Line"),
            cls.create_single_keyframe(duration_us, 0.0, curve_type="Line")
        ]

        return [
            cls.create_property_group(prop, kfs),
            cls.create_property_group(other_prop, other_kfs)
        ]

    @classmethod
    def preset_rhythmic_pulse_step(
        cls,
        duration_us: int,
        interval_seconds: float = 1.0,  # Nhịp 1s, 2s, 0.8s...
        motion_type: str = "bounce",    # "bounce" (nảy phóng to), "slide_up", "shake"
        bounce_scale: float = 1.15,
        bounce_duration_ms: int = 150
    ) -> List[Dict[str, Any]]:
        """
        Tạo chuỗi keyframe chuyển động lặp lại theo nhịp đều đặn (mỗi 1s, 2s...) trên một clip dài.
        """
        step_us = int(interval_seconds * 1_000_000)
        if step_us <= 0:
            step_us = 1_000_000

        pulse_us = bounce_duration_ms * 1000
        attack_us = int(pulse_us * 0.35)
        decay_us = pulse_us - attack_us

        scale_kfs = []
        pos_y_kfs = []

        scale_kfs.append(cls.create_single_keyframe(0, 1.0, curve_type="Line"))
        if motion_type == "slide_up":
            pos_y_kfs.append(cls.create_single_keyframe(0, 0.0, curve_type="Line"))

        cur_beat_t = 0
        while cur_beat_t < duration_us:
            t_start = max(0, cur_beat_t - attack_us)
            t_peak = cur_beat_t
            t_end = min(duration_us, cur_beat_t + decay_us)

            if motion_type == "bounce":
                scale_kfs.append(cls.create_single_keyframe(t_start, 1.0, curve_type="FreeCurveInOut"))
                scale_kfs.append(cls.create_single_keyframe(t_peak, bounce_scale, curve_type="FreeCurveInOut"))
                scale_kfs.append(cls.create_single_keyframe(t_end, 1.0, curve_type="FreeCurveInOut"))
            elif motion_type == "slide_up":
                scale_kfs.append(cls.create_single_keyframe(t_start, 1.0, curve_type="FreeCurveInOut"))
                scale_kfs.append(cls.create_single_keyframe(t_peak, 1.05, curve_type="FreeCurveInOut"))
                scale_kfs.append(cls.create_single_keyframe(t_end, 1.0, curve_type="FreeCurveInOut"))

                pos_y_kfs.append(cls.create_single_keyframe(t_start, 0.0, curve_type="FreeCurveInOut"))
                pos_y_kfs.append(cls.create_single_keyframe(t_peak, 0.06, curve_type="FreeCurveInOut"))
                pos_y_kfs.append(cls.create_single_keyframe(t_end, 0.0, curve_type="FreeCurveInOut"))

            cur_beat_t += step_us

        # Hold end
        if scale_kfs[-1]["time_offset"] < duration_us:
            scale_kfs.append(cls.create_single_keyframe(duration_us, 1.0, curve_type="Line"))
        if pos_y_kfs and pos_y_kfs[-1]["time_offset"] < duration_us:
            pos_y_kfs.append(cls.create_single_keyframe(duration_us, 0.0, curve_type="Line"))

        groups = [cls.create_property_group("KFTypeScaleX", scale_kfs)]
        if pos_y_kfs:
            groups.append(cls.create_property_group("KFTypePositionY", pos_y_kfs))

        return groups

    # ==========================================
    # PRESETS GENERATOR
    # ==========================================

    @classmethod
    def preset_smooth_zoom(
        cls,
        duration_us: int,
        start_scale: float = 1.0,
        end_scale: float = 1.25,
        curve_mode: str = "smooth",  # "smooth", "ease_in", "ease_out", "linear"
        zoom_duration_us: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates Smooth Zoom In/Out keyframes on KFTypeScaleX.
        """
        effect_dur = zoom_duration_us if zoom_duration_us and zoom_duration_us <= duration_us else duration_us

        if curve_mode == "linear":
            kf1 = cls.create_single_keyframe(0, start_scale, curve_type="Line")
            kf2 = cls.create_single_keyframe(effect_dur, end_scale, curve_type="Line")
        else:
            # Smooth Bezier S-Curve with right_control on start and left_control on end
            tangent_dx = float(effect_dur * 0.4)
            kf1 = cls.create_single_keyframe(
                0,
                start_scale,
                curve_type="FreeCurveInOut",
                right_control={"x": tangent_dx, "y": 0.0}
            )
            kf2 = cls.create_single_keyframe(
                effect_dur,
                end_scale,
                curve_type="FreeCurveInOut",
                left_control={"x": 0.0, "y": 0.0}
            )

        return [cls.create_property_group("KFTypeScaleX", [kf1, kf2])]

    @classmethod
    def preset_slow_pan(
        cls,
        duration_us: int,
        direction: str = "right",  # "right", "left", "up", "down", "diagonal_up_right"
        pan_distance: float = 0.15,
        zoom_scale: float = 1.15
    ) -> List[Dict[str, Any]]:
        """
        Cinematic slow pan (Ken Burns) with subtle zoom.
        """
        # Direction mapping to (start_x, start_y) -> (end_x, end_y)
        dx, dy = 0.0, 0.0
        if direction == "right":
            start_x, end_x = -pan_distance / 2, pan_distance / 2
            start_y, end_y = 0.0, 0.0
        elif direction == "left":
            start_x, end_x = pan_distance / 2, -pan_distance / 2
            start_y, end_y = 0.0, 0.0
        elif direction == "up":
            start_x, end_x = 0.0, 0.0
            start_y, end_y = -pan_distance / 2, pan_distance / 2
        elif direction == "down":
            start_x, end_x = 0.0, 0.0
            start_y, end_y = pan_distance / 2, -pan_distance / 2
        else:  # diagonal
            start_x, end_x = -pan_distance / 2, pan_distance / 2
            start_y, end_y = -pan_distance / 2, pan_distance / 2

        # Scale group
        scale_kf = [
            cls.create_single_keyframe(0, zoom_scale, curve_type="Line"),
            cls.create_single_keyframe(duration_us, zoom_scale * 1.05, curve_type="Line")
        ]
        # Position X group
        pos_x_kf = [
            cls.create_single_keyframe(0, start_x, curve_type="FreeCurveInOut", right_control={"x": float(duration_us * 0.35), "y": 0.0}),
            cls.create_single_keyframe(duration_us, end_x, curve_type="FreeCurveInOut")
        ]
        # Position Y group
        pos_y_kf = [
            cls.create_single_keyframe(0, start_y, curve_type="FreeCurveInOut", right_control={"x": float(duration_us * 0.35), "y": 0.0}),
            cls.create_single_keyframe(duration_us, end_y, curve_type="FreeCurveInOut")
        ]

        return [
            cls.create_property_group("KFTypeScaleX", scale_kf),
            cls.create_property_group("KFTypePositionX", pos_x_kf),
            cls.create_property_group("KFTypePositionY", pos_y_kf)
        ]

    @classmethod
    def preset_camera_shake(
        cls,
        duration_us: int,
        intensity: float = 0.03,      # Normalized screen displacement (0.01 - 0.1)
        frequency_hz: float = 12.0,   # Shakes per second (8 - 25 Hz)
        rotation_deg: float = 1.0,    # Max rotation angle in degrees
        decay: bool = False,          # Decay towards the end
        seed: int = 42
    ) -> List[Dict[str, Any]]:
        """
        Creates smooth, cinema-grade camera shake keyframes.
        """
        rng = random.Random(seed)
        step_us = int(1_000_000 / frequency_hz)
        num_steps = max(2, int(duration_us / step_us))

        pos_x_kfs = []
        pos_y_kfs = []
        rot_kfs = []

        for i in range(num_steps + 1):
            t_us = min(i * step_us, duration_us)
            progress = t_us / float(duration_us) if duration_us > 0 else 0

            # Compute decay factor
            factor = (1.0 - progress) if decay else 1.0
            # Ease in first 10% and ease out last 10%
            if progress < 0.1:
                factor *= (progress / 0.1)
            elif progress > 0.9:
                factor *= ((1.0 - progress) / 0.1)

            if i == 0 or i == num_steps:
                x_val, y_val, r_val = 0.0, 0.0, 0.0
            else:
                x_val = (rng.uniform(-1.0, 1.0)) * intensity * factor
                y_val = (rng.uniform(-1.0, 1.0)) * intensity * factor
                r_val = (rng.uniform(-1.0, 1.0)) * rotation_deg * factor

            # Use FreeCurveInOut with small tangent handles for organic smoothness
            handle_dx = float(step_us * 0.35)
            pos_x_kfs.append(cls.create_single_keyframe(
                t_us, x_val, curve_type="FreeCurveInOut",
                right_control={"x": handle_dx, "y": 0.0}
            ))
            pos_y_kfs.append(cls.create_single_keyframe(
                t_us, y_val, curve_type="FreeCurveInOut",
                right_control={"x": handle_dx, "y": 0.0}
            ))
            rot_kfs.append(cls.create_single_keyframe(
                t_us, r_val, curve_type="FreeCurveInOut",
                right_control={"x": handle_dx, "y": 0.0}
            ))

        # Also add a slight scale (e.g. 1.08) so screen edges don't show black during shaking
        min_scale = 1.0 + (intensity * 2.0)
        scale_kf = [
            cls.create_single_keyframe(0, min_scale, curve_type="Line"),
            cls.create_single_keyframe(duration_us, min_scale, curve_type="Line")
        ]

        return [
            cls.create_property_group("KFTypeScaleX", scale_kf),
            cls.create_property_group("KFTypePositionX", pos_x_kfs),
            cls.create_property_group("KFTypePositionY", pos_y_kfs),
            cls.create_property_group("KFTypeRotation", rot_kfs)
        ]

    @classmethod
    def preset_elastic_bounce(
        cls,
        duration_us: int,
        peak_scale: float = 1.25,
        base_scale: float = 1.0,
        bounce_duration_ms: int = 600
    ) -> List[Dict[str, Any]]:
        """
        Elastic pop/bounce animation (overshoot effect).
        """
        total_effect_us = min(duration_us, bounce_duration_ms * 1000)
        # Stages: 0.0 -> peak -> valley -> minor peak -> settle
        stages = [
            (0.00, base_scale),
            (0.25, peak_scale),
            (0.50, base_scale - (peak_scale - base_scale) * 0.25),
            (0.75, base_scale + (peak_scale - base_scale) * 0.12),
            (1.00, base_scale)
        ]

        kfs = []
        for frac, s_val in stages:
            t_us = int(frac * total_effect_us)
            kfs.append(cls.create_single_keyframe(
                t_us,
                round(s_val, 4),
                curve_type="FreeCurveInOut",
                right_control={"x": float(total_effect_us * 0.08), "y": 0.0}
            ))

        # Hold rest of clip at base_scale
        if total_effect_us < duration_us:
            kfs.append(cls.create_single_keyframe(duration_us, base_scale, curve_type="Line"))

        return [cls.create_property_group("KFTypeScaleX", kfs)]

    @classmethod
    def preset_whip_pan(
        cls,
        duration_us: int,
        direction: str = "right",  # "left", "right", "up", "down"
        whip_duration_ms: int = 350,
        is_transition_out: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fast whip pan transition keyframes.
        """
        whip_us = min(duration_us, whip_duration_ms * 1000)
        off_distance = 1.2  # completely off frame

        if is_transition_out:
            start_t = max(0, duration_us - whip_us)
            end_t = duration_us
            val1 = 0.0
            val2 = off_distance if direction in ["right", "up"] else -off_distance
        else:
            start_t = 0
            end_t = whip_us
            val1 = -off_distance if direction in ["right", "up"] else off_distance
            val2 = 0.0

        prop = "KFTypePositionX" if direction in ["left", "right"] else "KFTypePositionY"

        kfs = [
            cls.create_single_keyframe(start_t, val1, curve_type="FreeCurveInOut", right_control={"x": float(whip_us * 0.3), "y": 0.0}),
            cls.create_single_keyframe(end_t, val2, curve_type="FreeCurveInOut")
        ]

        # Slight zoom during whip
        scale_kfs = [
            cls.create_single_keyframe(start_t, 1.0, curve_type="FreeCurveInOut"),
            cls.create_single_keyframe(start_t + int(whip_us * 0.5), 1.15, curve_type="FreeCurveInOut"),
            cls.create_single_keyframe(end_t, 1.0, curve_type="FreeCurveInOut")
        ]

        return [
            cls.create_property_group(prop, kfs),
            cls.create_property_group("KFTypeScaleX", scale_kfs)
        ]

    @classmethod
    def preset_breathing_pulse(
        cls,
        duration_us: int,
        min_scale: float = 1.0,
        max_scale: float = 1.08,
        period_seconds: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Gentle periodic breathing/pulse oscillation.
        """
        period_us = int(period_seconds * 1_000_000)
        half_period_us = period_us // 2
        num_cycles = max(1, int(duration_us / period_us) + 1)

        kfs = []
        cur_t = 0
        state = 0  # 0: min_scale, 1: max_scale

        while cur_t <= duration_us:
            val = max_scale if state % 2 == 1 else min_scale
            kfs.append(cls.create_single_keyframe(
                cur_t,
                val,
                curve_type="FreeCurveInOut",
                right_control={"x": float(half_period_us * 0.4), "y": 0.0}
            ))
            cur_t += half_period_us
            state += 1

        if kfs[-1]["time_offset"] < duration_us:
            kfs.append(cls.create_single_keyframe(duration_us, min_scale, curve_type="Line"))

        return [cls.create_property_group("KFTypeScaleX", kfs)]

    @classmethod
    def preset_fade_opacity(
        cls,
        duration_us: int,
        fade_type: str = "in",  # "in", "out", "in_and_out"
        fade_duration_ms: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Smooth opacity fade in / fade out (KFTypeAlpha).
        """
        fade_us = min(duration_us // 2, fade_duration_ms * 1000)
        kfs = []

        if fade_type == "in":
            kfs.append(cls.create_single_keyframe(0, 0.0, curve_type="FreeCurveInOut", right_control={"x": float(fade_us * 0.4), "y": 0.0}))
            kfs.append(cls.create_single_keyframe(fade_us, 1.0, curve_type="FreeCurveInOut"))
            kfs.append(cls.create_single_keyframe(duration_us, 1.0, curve_type="Line"))
        elif fade_type == "out":
            kfs.append(cls.create_single_keyframe(0, 1.0, curve_type="Line"))
            kfs.append(cls.create_single_keyframe(max(0, duration_us - fade_us), 1.0, curve_type="FreeCurveInOut", right_control={"x": float(fade_us * 0.4), "y": 0.0}))
            kfs.append(cls.create_single_keyframe(duration_us, 0.0, curve_type="FreeCurveInOut"))
        else:  # in_and_out
            kfs.append(cls.create_single_keyframe(0, 0.0, curve_type="FreeCurveInOut", right_control={"x": float(fade_us * 0.4), "y": 0.0}))
            kfs.append(cls.create_single_keyframe(fade_us, 1.0, curve_type="FreeCurveInOut"))
            kfs.append(cls.create_single_keyframe(max(fade_us, duration_us - fade_us), 1.0, curve_type="FreeCurveInOut", right_control={"x": float(fade_us * 0.4), "y": 0.0}))
            kfs.append(cls.create_single_keyframe(duration_us, 0.0, curve_type="FreeCurveInOut"))

        return [cls.create_property_group("KFTypeAlpha", kfs)]

    # ==========================================
    # AUDIO BEAT SYNC KEYFRAMING
    # ==========================================

    @classmethod
    def generate_beat_bounce_keyframes(
        cls,
        segment_start_us: int,
        segment_duration_us: int,
        beat_timestamps_us: List[int],
        bounce_scale: float = 1.18,
        bounce_duration_ms: int = 140,
        mode: str = "bounce"  # "bounce", "shake", "flash"
    ) -> List[Dict[str, Any]]:
        """
        Generates dynamic keyframes synchronized to audio beats/bass.
        """
        seg_end_us = segment_start_us + segment_duration_us
        # Filter beats that fall inside this segment
        relevant_beats = [
            b - segment_start_us
            for b in beat_timestamps_us
            if segment_start_us <= b < seg_end_us
        ]

        if not relevant_beats:
            return []

        bounce_us = bounce_duration_ms * 1000
        attack_us = int(bounce_us * 0.35)
        decay_us = bounce_us - attack_us

        scale_kfs = []
        pos_x_kfs = []
        pos_y_kfs = []
        alpha_kfs = []

        # Start baseline at 0
        scale_kfs.append(cls.create_single_keyframe(0, 1.0, curve_type="Line"))
        if mode == "shake":
            pos_x_kfs.append(cls.create_single_keyframe(0, 0.0, curve_type="Line"))
            pos_y_kfs.append(cls.create_single_keyframe(0, 0.0, curve_type="Line"))
        elif mode == "flash":
            alpha_kfs.append(cls.create_single_keyframe(0, 1.0, curve_type="Line"))

        last_peak_t = -1

        for beat_t in relevant_beats:
            # Prevent overlapping too closely
            if beat_t - last_peak_t < bounce_us // 2:
                continue

            t_start = max(0, beat_t - attack_us)
            t_peak = beat_t
            t_end = min(segment_duration_us, beat_t + decay_us)

            if mode in ["bounce", "shake"]:
                # Scale bounce
                scale_kfs.append(cls.create_single_keyframe(
                    t_start, 1.0, curve_type="FreeCurveInOut",
                    right_control={"x": float(attack_us * 0.4), "y": 0.0}
                ))
                scale_kfs.append(cls.create_single_keyframe(
                    t_peak, bounce_scale, curve_type="FreeCurveInOut",
                    right_control={"x": float(decay_us * 0.4), "y": 0.0}
                ))
                scale_kfs.append(cls.create_single_keyframe(
                    t_end, 1.0, curve_type="FreeCurveInOut"
                ))

            if mode == "shake":
                # Quick directional snap
                snap_x = random.choice([-1, 1]) * 0.03
                snap_y = random.choice([-1, 1]) * 0.02
                pos_x_kfs.append(cls.create_single_keyframe(t_start, 0.0, curve_type="Line"))
                pos_x_kfs.append(cls.create_single_keyframe(t_peak, snap_x, curve_type="Line"))
                pos_x_kfs.append(cls.create_single_keyframe(t_end, 0.0, curve_type="Line"))

                pos_y_kfs.append(cls.create_single_keyframe(t_start, 0.0, curve_type="Line"))
                pos_y_kfs.append(cls.create_single_keyframe(t_peak, snap_y, curve_type="Line"))
                pos_y_kfs.append(cls.create_single_keyframe(t_end, 0.0, curve_type="Line"))

            if mode == "flash":
                alpha_kfs.append(cls.create_single_keyframe(t_start, 1.0, curve_type="Line"))
                alpha_kfs.append(cls.create_single_keyframe(t_peak, 0.6, curve_type="Line"))
                alpha_kfs.append(cls.create_single_keyframe(t_end, 1.0, curve_type="Line"))

            last_peak_t = t_end

        # Deduplicate & sort by time_offset
        def sort_and_clean(kflist):
            seen_times = {}
            for kf in kflist:
                t = kf["time_offset"]
                seen_times[t] = kf
            return [seen_times[t] for t in sorted(seen_times.keys())]

        result = []
        if scale_kfs:
            result.append(cls.create_property_group("KFTypeScaleX", sort_and_clean(scale_kfs)))
        if pos_x_kfs and pos_y_kfs:
            result.append(cls.create_property_group("KFTypePositionX", sort_and_clean(pos_x_kfs)))
            result.append(cls.create_property_group("KFTypePositionY", sort_and_clean(pos_y_kfs)))
        if alpha_kfs:
            result.append(cls.create_property_group("KFTypeAlpha", sort_and_clean(alpha_kfs)))

        return result

    # ==========================================
    # BATCH REPLICATION & CURVE SMOOTHING
    # ==========================================

    @classmethod
    def replicate_keyframes(
        cls,
        source_keyframes: List[Dict[str, Any]],
        source_duration_us: int,
        target_duration_us: int,
        mode: str = "stretch"  # "stretch" or "fixed"
    ) -> List[Dict[str, Any]]:
        """
        Replicates keyframes from a source segment onto a target segment.
        Generates brand new UUIDs and optionally stretches time proportionally.
        """
        replicated = []
        scale_ratio = (target_duration_us / float(source_duration_us)) if (mode == "stretch" and source_duration_us > 0) else 1.0

        for prop_group in source_keyframes:
            ptype = prop_group.get("property_type", "")
            orig_list = prop_group.get("keyframe_list", [])
            new_list = []

            for kf in orig_list:
                orig_t = kf.get("time_offset", 0)
                new_t = int(orig_t * scale_ratio)
                if new_t > target_duration_us:
                    new_t = target_duration_us

                left_ctrl = dict(kf.get("left_control", {"x": 0.0, "y": 0.0}))
                right_ctrl = dict(kf.get("right_control", {"x": 0.0, "y": 0.0}))
                if mode == "stretch":
                    left_ctrl["x"] = left_ctrl.get("x", 0.0) * scale_ratio
                    right_ctrl["x"] = right_ctrl.get("x", 0.0) * scale_ratio

                new_kf = {
                    "id": cls.generate_uuid(),
                    "curveType": kf.get("curveType", "Line"),
                    "time_offset": new_t,
                    "left_control": left_ctrl,
                    "right_control": right_ctrl,
                    "values": list(kf.get("values", [1.0])),
                    "string_value": kf.get("string_value", ""),
                    "graphID": ""
                }
                new_list.append(new_kf)

            replicated.append({
                "id": cls.generate_uuid(),
                "material_id": "",
                "property_type": ptype,
                "keyframe_list": new_list
            })

        return replicated

    @classmethod
    def convert_to_smooth_curves(
        cls,
        keyframes: List[Dict[str, Any]],
        smoothness: float = 0.35  # Tangent length ratio (0.1 - 0.5)
    ) -> List[Dict[str, Any]]:
        """
        Converts all 'Line' keyframes into smooth 'FreeCurveInOut' Bezier curves.
        """
        smoothed_groups = []
        for prop_group in keyframes:
            new_group = dict(prop_group)
            klist = [dict(k) for k in prop_group.get("keyframe_list", [])]

            for i in range(len(klist)):
                cur_kf = klist[i]
                cur_t = cur_kf["time_offset"]

                # Calculate right_control towards next keyframe
                if i < len(klist) - 1:
                    next_t = klist[i + 1]["time_offset"]
                    dt = next_t - cur_t
                    cur_kf["curveType"] = "FreeCurveInOut"
                    cur_kf["right_control"] = {
                        "x": float(dt * smoothness),
                        "y": 0.0  # Horizontal tangent creates effortless ease-in/ease-out
                    }

                # Calculate left_control from previous keyframe
                if i > 0:
                    prev_t = klist[i - 1]["time_offset"]
                    dt = cur_t - prev_t
                    cur_kf["left_control"] = {
                        "x": float(-dt * smoothness),
                        "y": 0.0
                    }

            new_group["keyframe_list"] = klist
            smoothed_groups.append(new_group)

        return smoothed_groups

    @classmethod
    def shift_keyframes(
        cls,
        keyframes: List[Dict[str, Any]],
        delta_us: int,
        max_duration_us: int
    ) -> List[Dict[str, Any]]:
        """
        Shifts all keyframes by delta_us (forward or backward).
        """
        shifted = []
        for prop_group in keyframes:
            new_group = dict(prop_group)
            klist = []
            for kf in prop_group.get("keyframe_list", []):
                new_kf = dict(kf)
                new_t = max(0, min(max_duration_us, new_kf["time_offset"] + delta_us))
                new_kf["time_offset"] = new_t
                klist.append(new_kf)
            new_group["keyframe_list"] = klist
            shifted.append(new_group)
        return shifted
