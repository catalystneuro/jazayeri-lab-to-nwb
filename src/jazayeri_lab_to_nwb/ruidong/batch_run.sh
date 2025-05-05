#!/bin/bash

# Define the path to the data file
file_path="subject_names.csv"

# Loop through each line in the CSV file, skipping the header
tail -n +2 "$file_path" | while IFS=',' read -r session date trialtype subject1 subject2
do
    # Trim leading and trailing whitespaces from the fields
    subject1=$(echo "$subject1" | xargs)
    subject2=$(echo "$subject2" | xargs)

    # Check if subject1 is "O"
    if [[ "$subject1" == "O" ]]; then
        # Run the command for subject1 "O"
        sbatch --partition=jazayeri --mem=4GB --mail-user=ruidong@mit.edu --mail-type=FAIL,CANCEL \
               --wrap="touch /om2/user/ruidong/data/data_srl/social_O_L/$date/results/v_probe_1/data.dat; python main_convert_session.py Offenbach $date"
    fi

    # Check if subject1 is "L"
    if [[ "$subject1" == "L" ]]; then
        # Run the command for subject1 "L"
        sbatch --partition=jazayeri --mem=4GB --mail-user=ruidong@mit.edu --mail-type=FAIL,CANCEL \
               --wrap="touch /om2/user/ruidong/data/data_srl/social_O_L/$date/results/v_probe_1/data.dat; python main_convert_session.py Lalo $date"
    fi

    # Check if subject2 is "O"
    if [[ "$subject2" == "O" ]]; then
        # Run the command for subject2 "O"
        sbatch --partition=jazayeri --mem=4GB --mail-user=ruidong@mit.edu --mail-type=FAIL,CANCEL \
               --wrap="touch /om2/user/ruidong/data/data_srl/social_O_L/$date/results/v_probe_2/data.dat; python main_convert_session.py Offenbach $date"
    fi
done