import os
import json
import argparse
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

def get_scores(data_dir):

    file_paths = []
    for root, _, files in os.walk(data_dir):
        new_files = [os.path.join(root, f) for f in files
                   if f.endswith('.json') and not f.startswith('trajectory_variants')]
        file_paths += new_files
    
    scores = []

    for f in tqdm(file_paths):
        with open(f, 'r') as traj_file:
            trajectory_data = json.load(traj_file)
            score = int(trajectory_data['label']*100)
            scores.append(score)

    return np.array(scores)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Show the score distribution in the dataset')

    parser.add_argument('--dataset', type=str, nargs='?', required=True, help='Directory containing the labeled dataset')
    args = parser.parse_args()

    dataset_dir = args.dataset
    nbins = 10
    scores = get_scores(dataset_dir)
    plt.hist(scores, bins=np.arange(0, 101, 100//nbins), color='skyblue', edgecolor='black')

    plt.title('Score distribution')
    plt.xlabel('scores')
    plt.ylabel('trajectories')

    plt.show()
