#!/usr/bin/env bash
# submit_sessions.sh  –  queue a job for every session in subject_names.csv
# Adds robust CR‑stripping and DEBUG output for easy tracing.

set -euo pipefail

CSV="subject_names.csv"            # change if the CSV lives elsewhere
PARTITION="jazayeri"
MEM="4G"
EMAIL="ruidong@mit.edu"
MAIL_FLAGS="FAIL,CANCEL"

# Turn on bash tracing with:  DEBUG=1 ./submit_sessions.sh
[[ ${DEBUG:-0} == 1 ]] && set -x

# Skip header, process each record
tail -n +2 "$CSV" | while IFS=',' read -r session date trial_type subject1 subject2 _
do
    # ----- Clean up fields -----
    # 1) Strip DOS CR, 2) trim whitespace
    date=$(echo "$date"      | tr -d '\r' | xargs)
    subject1=$(echo "$subject1" | tr -d '\r' | xargs)
    subject2=$(echo "$subject2" | tr -d '\r' | xargs)

    [[ $DEBUG == 1 ]] && echo "DEBUG: date=$date  subj1=$subject1  subj2=$subject2"

    # ----------  subject 1  (v_probe_1) ----------
    case "$subject1" in
        O)
            CMD="touch /om2/user/ruidong/data/data_srl/social_O_L/${date}/results/v_probe_1/data.dat; \
                 python main_convert_session.py Offenbach ${date}"
            ;;
        L)
            CMD="touch /om2/user/ruidong/data/data_srl/social_O_L/${date}/results/v_probe_1/data.dat; \
                 python main_convert_session.py Lalo ${date}"
            ;;
        *)
            echo "DEBUG: Unrecognised subject1 value '$subject1' – skipping" >&2
            CMD=""
            ;;
    esac
    [[ -n $CMD ]] && {
        echo "DEBUG: queuing v_probe_1 job → $CMD"
        sbatch --partition="$PARTITION" --mem="$MEM" \
               --mail-user="$EMAIL" --mail-type="$MAIL_FLAGS" \
               --wrap="$CMD"
    }

    # ----------  subject 2  (v_probe_2) ----------
    case "$subject2" in
        O)
            CMD="touch /om2/user/ruidong/data/data_srl/social_O_L/${date}/results/v_probe_2/data.dat; \
                 python main_convert_session.py Offenbach ${date}"
            ;;
        L)
            CMD="touch /om2/user/ruidong/data/data_srl/social_O_L/${date}/results/v_probe_2/data.dat; \
                 python main_convert_session.py Lalo ${date}"
            ;;
        *)
            echo "DEBUG: Unrecognised subject2 value '$subject2' – skipping" >&2
            CMD=""
            ;;
    esac
    [[ -n $CMD ]] && {
        echo "DEBUG: queuing v_probe_2 job → $CMD"
        sbatch --partition="$PARTITION" --mem="$MEM" \
               --mail-user="$EMAIL" --mail-type="$MAIL_FLAGS" \
               --wrap="$CMD"
    }
done
