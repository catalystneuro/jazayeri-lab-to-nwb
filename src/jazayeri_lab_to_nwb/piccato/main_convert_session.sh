#!/bin/sh

#SBATCH -o /om2/user/apiccato/jazayeri-lab-to-nwb/src/jazayeri_lab_to_nwb/piccato/logs/%A.out
#SBATCH -t 99:00:00
#SBATCH -n 1
#SBATCH --mem-per-cpu 30G
#SBATCH --mail-type=NONE
#SBATCH --mail-user=apiccato@mit.edu
#SBATCH --partition=jazayeri

# Script to convert a session to NWB format. Takes in two arguments from user:
# name of subject and session date. 


SUBJECT=$1  # Argument passed in by user. Should be in subject/date format
echo "SUBJECT: $SUBJECT"
if [ -z "$SUBJECT" ]; then
    echo "No session specified, exiting."
    exit
fi

SESSION=$2  # Argument passed in by user. Should be in subject/date format
echo "SESSION: $SESSION"
if [ -z "$SESSION" ]; then
    echo "No session specified, exiting."
    exit
fi

source ~/.bashrc
conda activate jazayeri_lab_to_nwb_env
cd /om2/user/apiccato/jazayeri-lab-to-nwb
python src/jazayeri_lab_to_nwb/piccato/main_convert_session.py $SUBJECT $SESSION