import os
import json
import argparse
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

def get_scores(datadir, use_raters):

    file_paths = []
    for root, _, files in os.walk(datadir):
        new_files = [os.path.join(root, f) for f in files
                   if f.endswith('.json') and not f.startswith('trajectory_variants')]
        file_paths += new_files
    
    scores = []

    if use_raters:
        control_indices = [3007,2007,1007,7,302,1302,2302,3102,2002,1002,2,3094,2894,1879,834]
        for f in tqdm(file_paths):
            with open(f, 'r') as rater_file:
                raw_data = rater_file.read()
                # Remove invalid characters
                sanitized_data = raw_data.replace('\n', '').replace('\t', '')
                rater_data = json.loads(sanitized_data)
                answers = rater_data['answers']
                trajectories = rater_data['indices']
                for a in answers:
                    idx = trajectories[int(a)]
                    if idx not in control_indices:
                        score = int(answers[a]*100)
                        scores.append(score)
    else:
        for f in tqdm(file_paths):
            with open(f, 'r') as traj_file:
                trajectory_data = json.load(traj_file)
                if 'label' in trajectory_data.keys():
                    score = int(trajectory_data['label']*100)
                    scores.append(score)
                else:
                    print(f'The trajectory file {f} does not have a correct format. If you one to use the raters file, add the argument --use_raters')

    return np.array(scores)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Show the score distribution in the dataset')

    parser.add_argument('--datadir', type=str, nargs='?', required=True, help='Directory containing the labeled dataset')
    parser.add_argument('--nbins', type=int, default = 10, help='Number of bins of the histogram')
    parser.add_argument('--use_raters', action='store_true', help='Use raters\' files')
    args = parser.parse_args()

    datadir = args.datadir
    nbins = args.nbins
    use_raters = args.use_raters
    scores = get_scores(datadir, use_raters)
    plt.hist(scores, bins=np.arange(0, 101, 100//nbins), color='skyblue', edgecolor='black')

    plt.title('Score distribution')
    plt.xlabel('scores')
    plt.ylabel('trajectories')

    plt.show()
