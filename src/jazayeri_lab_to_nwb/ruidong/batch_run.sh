#!/usr/bin/env bash
# submit_sessions.sh  –  queue one SLURM job per session in subject_names.csv
# Requirements:  subject_names.csv must sit in the same directory as this script.

set -euo pipefail

CSV="subject_names.csv"            # path to the input file
PARTITION="jazayeri"
MEM="4G"
EMAIL="ruidong@mit.edu"
MAIL_FLAGS="FAIL,CANCEL"

# Skip header and process each record
tail -n +2 "$CSV" | while IFS=',' read -r session date trial_type subject1 subject2 _
do
    # Strip DOS CR characters and trim whitespace
    date=$(echo "$date"      | tr -d '\r' | xargs)
    subject1=$(echo "$subject1" | tr -d '\r' | xargs)
    subject2=$(echo "$subject2" | tr -d '\r' | xargs)

    # ----------  subject 1  (v_probe_1) ----------
    if [[ "$subject1" == "O" || "$subject1" == "L" ]]; then
        performer1=$([[ "$subject1" == "O" ]] && echo "Offenbach" || echo "Lalo")
        sbatch --partition="$PARTITION" --mem="$MEM" \
               --mail-user="$EMAIL" --mail-type="$MAIL_FLAGS" \
               --wrap="touch /om2/user/ruidong/data/data_srl/social_O_L/${date}/results/v_probe_1/data.dat; \
                       python main_convert_session.py ${performer1} ${date}"
    fi

    # ----------  subject 2  (v_probe_2) ----------
    if [[ "$subject2" == "O" || "$subject2" == "L" ]]; then
        performer2=$([[ "$subject2" == "O" ]] && echo "Offenbach" || echo "Lalo")
        sbatch --partition="$PARTITION" --mem="$MEM" \
               --mail-user="$EMAIL" --mail-type="$MAIL_FLAGS" \
               --wrap="touch /om2/user/ruidong/data/data_srl/social_O_L/${date}/results/v_probe_2/data.dat; \
                       python main_convert_session.py ${performer2} ${date}"
    fi
done
