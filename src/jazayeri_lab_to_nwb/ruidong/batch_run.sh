#!/usr/bin/env bash
#
# submit_sessions.sh — queue one SLURM job per (date, subject) session,
# checking .dat size and copying the best source from /om4 if needed.

set -euo pipefail

# ─── Config ────────────────────────────────────────────────────────────────────

CSV="subject_names.csv"                          # input CSV (must exist here)
PARTITION="jazayeri"
MEM="4G"
EMAIL="ruidong@mit.edu"
MAIL_FLAGS="FAIL,CANCEL"

# ─── Function to generate & sbatch a small job‐script ───────────────────────────　

submit_job() {
  local date="$1"      # e.g. 2025-01-15
  local probe="$2"     # 1 or 2
  local performer="$3" # Offenbach or Lalo

  # Source & target paths
  local SRC_DIR="/om4/group/jazlab/ruidong/data/data_srl/social_O_L/${date}/results/v_probe_${probe}"
  local TARGET_FILE="/om2/user/ruidong/data/data_srl/social_O_L/${date}/results/v_probe_${probe}/data.dat"

  # Create a tiny per-job script so we can write multi-line checks clearly
  local JOBSCRIPT
  JOBSCRIPT=$(mktemp /tmp/job_${date}_p${probe}_XXXX.sh)

  cat > "$JOBSCRIPT" <<EOF
#!/usr/bin/env bash
set -euo pipefail

# ensure the output directory exists
mkdir -p "\$(dirname "$TARGET_FILE")"

# if data.dat exists and is ≥1 MB, skip copy
if [[ -f "$TARGET_FILE" && \$(stat -c%s "$TARGET_FILE") -ge 1048576 ]]; then
  echo "[\$(date)] $TARGET_FILE is ≥1 MB; no copy needed."
else
  # find the largest .dat in the source directory
  DAT_SRC=\$(find "$SRC_DIR" -maxdepth 1 -type f -name '*.dat' -printf '%s %p\n' \\
            | sort -nr \\
            | head -n1 \\
            | cut -d' ' -f2-)

  if [[ -n "\$DAT_SRC" ]]; then
    echo "[\$(date)] Copying \$DAT_SRC → $TARGET_FILE"
    cp "\$DAT_SRC" "$TARGET_FILE"
  else
    echo "[\$(date)] ERROR: no .dat files found in $SRC_DIR" >&2
  fi
fi

# finally, run your conversion
python main_convert_session.py $performer $date
EOF

  # make it runnable, then sbatch it
  chmod +x "$JOBSCRIPT"
  sbatch --partition="$PARTITION" \
         --mem="$MEM" \
         --mail-user="$EMAIL" \
         --mail-type="$MAIL_FLAGS" \
         "$JOBSCRIPT"
}

# ─── Main loop: read CSV and dispatch jobs ───────────────────────────────────────

# Skip header row, then read: session,date,trial_type,subject1,subject2,...
tail -n +2 "$CSV" | while IFS=',' read -r session date trial_type subject1 subject2 _; do
  # strip CRs + trim whitespace
  date=\$(echo "\$date"      | tr -d '\\r' | xargs)
  subject1=\$(echo "\$subject1" | tr -d '\\r' | xargs)
  subject2=\$(echo "\$subject2" | tr -d '\\r' | xargs)

  # subject1 → v_probe_1
  if [[ "\$subject1" == "O" || "\$subject1" == "L" ]]; then
    performer1=\$([[ "\$subject1" == "O" ]] && echo "Offenbach" || echo "Lalo")
    submit_job "\$date" 1 "\$performer1"
  fi

  # subject2 → v_probe_2
  if [[ "\$subject2" == "O" || "\$subject2" == "L" ]]; then
    performer2=\$([[ "\$subject2" == "O" ]] && echo "Offenbach" || echo "Lalo")
    submit_job "\$date" 2 "\$performer2"
  fi
done
