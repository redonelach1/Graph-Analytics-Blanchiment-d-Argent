"""
temporal_policy.py — Sliding Window & Watermark Management.

Implements Section 5 of project_plan_and_specifications.md:
- Window length L = 600s (10 minutes)
- Slide S = 30s
- Watermark W = H - 120s (2 minutes behind committed high-water mark H)
- Half-open intervals: window_start <= event_time < window_end
- UTC alignment
"""

import math
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple


class TemporalWindowPolicy:
    """Manages aligned sliding window calculations and watermark tracking."""

    def __init__(
        self,
        window_length_seconds: int = 600,
        slide_seconds: int = 30,
        watermark_seconds: int = 120,
    ):
        self.window_length = window_length_seconds
        self.slide = slide_seconds
        self.watermark_delay = watermark_seconds
        self.high_water_mark: Optional[datetime] = None

    def get_aligned_windows(self, event_time: datetime) -> List[Tuple[datetime, datetime]]:
        """
        Calculates all aligned sliding windows that contain the given event_time.
        Windows are half-open: window_start <= event_time < window_end.
        """
        # Ensure UTC timezone
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        else:
            event_time = event_time.astimezone(timezone.utc)

        ts = event_time.timestamp()

        # Window k spans: [k * slide, k * slide + window_length)
        # Therefore: k * slide <= ts < k * slide + window_length
        # => ts - window_length < k * slide <= ts
        # => (ts - window_length) / slide < k <= ts / slide
        min_k = math.floor((ts - self.window_length) / self.slide) + 1
        max_k = math.floor(ts / self.slide)

        windows = []
        for k in range(min_k, max_k + 1):
            w_start_epoch = k * self.slide
            w_end_epoch = w_start_epoch + self.window_length
            w_start = datetime.fromtimestamp(w_start_epoch, tz=timezone.utc)
            w_end = datetime.fromtimestamp(w_end_epoch, tz=timezone.utc)
            windows.append((w_start, w_end))

        return windows

    def is_in_window(
        self, event_time: datetime, window_start: datetime, window_end: datetime
    ) -> bool:
        """Checks half-open membership: window_start <= event_time < window_end."""
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)
        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=timezone.utc)
        if window_end.tzinfo is None:
            window_end = window_end.replace(tzinfo=timezone.utc)

        return window_start <= event_time < window_end

    def update_high_water_mark(self, latest_event_time: datetime) -> datetime:
        """Advances high-water mark H if the new event time is strictly greater."""
        if latest_event_time.tzinfo is None:
            latest_event_time = latest_event_time.replace(tzinfo=timezone.utc)

        if self.high_water_mark is None or latest_event_time > self.high_water_mark:
            self.high_water_mark = latest_event_time

        return self.high_water_mark

    def get_watermark(self) -> Optional[datetime]:
        """Returns W = H - watermark_delay (or None if no H yet)."""
        if self.high_water_mark is None:
            return None
        return self.high_water_mark - timedelta(seconds=self.watermark_delay)

    def is_late(self, event_time: datetime) -> bool:
        """
        Determines if event is late relative to current watermark W.
        Events with event_time < W are retrospective-only.
        Events with event_time >= W are eligible for online processing.
        """
        w = self.get_watermark()
        if w is None:
            return False  # No high water mark established yet

        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone.utc)

        return event_time < w

