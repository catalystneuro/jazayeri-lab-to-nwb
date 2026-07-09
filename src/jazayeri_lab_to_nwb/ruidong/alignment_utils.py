"""Utilities to align behavioral streams to the Open Ephys acquisition clock.

Background
----------
For subject 1 (and any two-rig session), eye position, joystick position, and
the MOOG trial table are each recorded on a *different* machine, and therefore
carry a *different* native clock:

    * eye position   -> EyeLink / MWorks server clock (mworks_events or
                        mworks_events_2nd_eyelink, depending on subject)
    * joystick        -> main MWorks server clock (mworks_events)
    * trials          -> MOOG Unix-epoch wall clock (moog_events/trial_info.csv)
    * spikes / units  -> Open Ephys acquisition clock (30 kHz), t=0 at
                        acquisition start.  THIS IS THE MASTER CLOCK.

The Open Ephys clock is the only one that cannot be shifted (spike times are
sample-indexed into the immutable ElectricalSeries), so every other stream is
mapped onto it.

The mapping is a linear transform ``t_oe = a * t_native + b`` per device clock,
fit from matched (native_trial_start, open_ephys_trial_start) anchor pairs.  The
anchors already exist in the ephys pipeline:

    * ``open_ephys_events/open_ephys_trials.json`` gives, per trial_num, the
      trial-start time ``t_start`` **in Open Ephys seconds** (derived from the
      TTL sync_trial_start / sync_trial_num signals in process_sync_vars.py).
    * Each device folder's ``trial_info.json`` gives, per trial_num, the
      trial-start time in that device's native clock.  (For MOOG the anchor is
      ``moog_events/trial_info.csv['trial_start_time']``.)

Joining on ``trial_num`` yields the anchor pairs, and a least-squares fit on
centered data gives ``a`` (captures inter-machine clock drift, typically tens of
ppm) and ``b`` (the offset).

This module is intentionally dependency-light (numpy + pandas + json) so it can
be imported inside the neuroconv interfaces or from main_convert_session.py.
"""

import json
import os
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd


@dataclass
class ClockTransform:
    """Linear map t_oe = a * t_native + b, fit from trial-start anchors."""

    a: float
    b: float
    n: int
    resid_med_ms: float
    resid_max_ms: float
    resid_rms_ms: float
    ppm_drift: float
    source: str = ""

    def apply(self, t):
        """Map native-clock timestamps onto the Open Ephys clock."""
        return self.a * np.asarray(t, dtype=float) + self.b

    def as_dict(self):
        return asdict(self)


def _fit_linear(t_native, t_oe, source=""):
    """Least-squares fit of t_oe = a*t_native + b, on mean-centered t_native.

    Centering is essential: raw MOOG timestamps are Unix seconds (~1.67e9) with
    a tiny relative range, so an uncentered design matrix is severely
    ill-conditioned and the slope collapses to ~0.
    """
    t_native = np.asarray(t_native, dtype=float)
    t_oe = np.asarray(t_oe, dtype=float)
    if len(t_native) < 2:
        raise ValueError(f"Need >=2 anchor pairs to fit a transform ({source}).")
    tn0 = t_native.mean()
    A = np.vstack([t_native - tn0, np.ones_like(t_native)]).T
    (a, b0), *_ = np.linalg.lstsq(A, t_oe, rcond=None)
    b = b0 - a * tn0  # convert intercept back to the un-centered clock
    resid = t_oe - (a * t_native + b)
    return ClockTransform(
        a=float(a),
        b=float(b),
        n=int(len(t_native)),
        resid_med_ms=float(np.median(np.abs(resid)) * 1e3),
        resid_max_ms=float(np.max(np.abs(resid)) * 1e3),
        resid_rms_ms=float(np.sqrt(np.mean(resid ** 2)) * 1e3),
        ppm_drift=float((a - 1.0) * 1e6),
        source=source,
    )


def load_oe_anchors(open_ephys_events_dir):
    """Load per-trial Open Ephys trial-start times (the master-clock anchors).

    Returns a DataFrame with columns ['trial_num', 't_start_oe'].
    """
    path = os.path.join(open_ephys_events_dir, "open_ephys_trials.json")
    with open(path, "r") as f:
        oe_trials = json.load(f)
    df = pd.DataFrame(
        [{"trial_num": int(t["trial_num"]), "t_start_oe": float(t["t_start"])}
         for t in oe_trials]
    )
    if df.empty:
        raise ValueError(f"No Open Ephys trials found in {path}")
    return df


def _fit_from_trial_info_json(trial_info_json_path, oe_df, source):
    """Fit device-clock -> OE from a folder's trial_info.json.

    trial_info.json entries have 'trial_num' and 'trial_start' in the device's
    native clock. Anchors are matched to OE on trial_num.
    """
    with open(trial_info_json_path, "r") as f:
        ti = json.load(f)
    dev = pd.DataFrame(
        [{"trial_num": int(t["trial_num"]), "t_native": float(t["trial_start"])}
         for t in ti]
    )
    merged = dev.merge(oe_df, on="trial_num", how="inner")
    if len(merged) < 2:
        raise ValueError(
            f"Only {len(merged)} matched anchors for {source}; cannot align."
        )
    return _fit_linear(merged.t_native.values, merged.t_start_oe.values, source)


def fit_moog_to_oe(moog_events_dir, oe_df):
    """Fit MOOG Unix-epoch clock -> Open Ephys clock (used for the trials table)."""
    csv = os.path.join(moog_events_dir, "trial_info.csv")
    df = pd.read_csv(csv)
    merged = df[["trial_num", "trial_start_time"]].merge(oe_df, on="trial_num", how="inner")
    if len(merged) < 2:
        raise ValueError("Fewer than 2 MOOG<->OE anchors; cannot align trials.")
    return _fit_linear(
        merged.trial_start_time.values, merged.t_start_oe.values, source="moog_unix"
    )


def read_recording_offset(offset_csv_path, fs=30000.0):
    """Read the Open-Ephys-events -> Kilosort/.dat recording clock offset.

    ``open_ephys_trials.json`` t_start values are on the ABSOLUTE Open Ephys
    acquisition clock (TTL sample_number / fs, counted from acquisition start).
    The published ``units`` (spike times), however, are 0-based on the Kilosort
    ``.dat`` recording clock -- the KiloSortSortingInterface does NOT add the
    recording-start offset that the analysis pipeline
    (spikes/get_spike_times_per_cluster.py) applies.

    To land behavior on the SAME clock as the immutable published units, we
    subtract this offset (in seconds) from the OE-referenced timestamps:

        t_units = a * t_native + b - offset_seconds

    ``offset.csv`` holds the first recording sample number (new Open Ephys), so
    ``offset_seconds = value / fs``.  Returns 0.0 if the path is None/missing
    (i.e. fall back to the absolute OE clock).
    """
    if offset_csv_path is None or not os.path.exists(offset_csv_path):
        return 0.0
    val = float(np.genfromtxt(offset_csv_path, delimiter=","))
    return val / fs


def build_session_transforms(eye_folder, joystick_folder, moog_events_dir,
                             open_ephys_events_dir, offset_csv_path=None,
                             fs=30000.0):
    """Fit all clock->recording-clock transforms needed for one session.

    Parameters
    ----------
    eye_folder : str
        Folder holding the eye trial_info.json for this subject
        (mworks_events for Offenbach, mworks_events_2nd_eyelink for Lalo).
    joystick_folder : str
        Folder holding the joystick trial_info.json (always mworks_events).
    moog_events_dir : str
        Folder holding moog_events/trial_info.csv.
    open_ephys_events_dir : str
        Folder holding open_ephys_trials.json (absolute-OE-clock anchors).
    offset_csv_path : str, optional
        Path to the probe's offset.csv (first recording sample number). When
        given, transforms map onto the 0-based Kilosort/.dat recording clock so
        they match the published ``units``. When None, transforms stay on the
        absolute Open Ephys clock (offset 0).
    fs : float
        Acquisition sample rate (Hz), default 30 kHz.

    Returns
    -------
    dict with keys 'eye', 'joystick', 'trials' -> ClockTransform, plus
    'offset_seconds' (float) recording the applied offset.
    """
    oe_df = load_oe_anchors(open_ephys_events_dir)
    offset_seconds = read_recording_offset(offset_csv_path, fs=fs)

    def _fit(path, src):
        t = _fit_from_trial_info_json(path, oe_df, source=src)
        # fold the recording-clock offset into the intercept
        t.b -= offset_seconds
        return t

    trials = fit_moog_to_oe(moog_events_dir, oe_df)
    trials.b -= offset_seconds

    transforms = {
        "eye": _fit(os.path.join(eye_folder, "trial_info.json"), "eye"),
        "joystick": _fit(os.path.join(joystick_folder, "trial_info.json"), "joystick"),
        "trials": trials,
        "offset_seconds": offset_seconds,
    }
    return transforms


def transforms_report(transforms):
    """Human-readable one-line-per-stream summary (for logging / QC)."""
    lines = []
    for name, t in transforms.items():
        if not isinstance(t, ClockTransform):
            continue
        lines.append(
            f"{name:9s} a={t.a:.9f} ({t.ppm_drift:+.1f} ppm) b={t.b:.4f}  "
            f"n={t.n}  resid med/rms/max ms = "
            f"{t.resid_med_ms:.2f}/{t.resid_rms_ms:.2f}/{t.resid_max_ms:.2f}"
        )
    return "\n".join(lines)
