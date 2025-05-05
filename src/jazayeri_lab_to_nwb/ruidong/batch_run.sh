#!/usr/bin/env bash
# submit_sessions.sh – launch conversion jobs for every session listed in subject_names.csv

CSV="subject_names.csv"                      # ↳ adjust if the file lives elsewhere

# Skip the header row, then read one record at a time
tail -n +2 "$CSV" | while IFS=',' read -r session date trial_type subject1 subject2
do
  # Trim possible whitespace that can appear after the commas
  date=$(echo "$date" | xargs)
  subject1=$(echo "$subject1" | xargs)
  subject2=$(echo "$subject2" | xargs)

  # ----------  subject 1 (v_probe_1) ----------
  case "$subject1" in
    O)
      sbatch --partition=jazayeri --mem=4G \
             --mail-user=ruidong@mit.edu --mail-type=FAIL,CANCEL \
             --wrap="touch /om2/user/ruidong/data/data_srl/social_O_L/${date}/results/v_probe_1/data.dat; \
                     python main_convert_session.py Offenbach ${date}"
      ;;
    L)
      sbatch --partition=jazayeri --mem=4G \
             --mail-user=ruidong@mit.edu --mail-type=FAIL,CANCEL \
             --wrap="touch /om2/user/ruidong/data/data_srl/social_O_L/${date}/results/v_probe_1/data.dat; \
                     python main_convert_session.py Lalo ${date}"
      ;;
  esac

  # ----------  subject 2 (v_probe_2) ----------
  case "$subject2" in
    O)
      sbatch --partition=jazayeri --mem=4G \
             --mail-user=ruidong@mit.edu --mail-type=FAIL,CANCEL \
             --wrap="touch /om2/user/ruidong/data/data_srl/social_O_L/${date}/results/v_probe_2/data.dat; \
                     python main_convert_session.py Offenbach ${date}"
      ;;
    L)
      sbatch --partition=jazayeri --mem=4G \
             --mail-user=ruidong@mit.edu --mail-type=FAIL,CANCEL \
             --wrap="touch /om2/user/ruidong/data/data_srl/social_O_L/${date}/results/v_probe_2/data.dat; \
                     python main_convert_session.py Lalo ${date}"
      ;;
  esac
done
