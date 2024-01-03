#!/bin/sh

#SBATCH -o /om2/user/apiccato/jazayeri-lab-to-nwb/src/jazayeri_lab_to_nwb/piccato/logs/%A.out
#SBATCH -t 06:00:00
#SBATCH -n 1
#SBATCH --mem-per-cpu 30G
#SBATCH --mail-type=NONE
#SBATCH --mail-user=apiccato@mit.edu
#SBATCH --partition=jazayeri

source ~/.bashrc
conda activate jazayeri_lab_to_nwb_env
cd /om2/user/apiccato/jazayeri-lab-to-nwb
python src/jazayeri_lab_to_nwb/piccato/main_convert_session.py elgar 2023-11-30