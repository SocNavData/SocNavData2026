import os
import random
import json
import argparse
import numpy as np
from tqdm import tqdm

def data_splitter(data_dir, train_ratio, val_ratio, test_ratio):

    trajectory_variant = dict()
    variants_path = os.path.join(data_dir, 'trajectory_variants.json')
    with open(variants_path, 'r') as traj_file:
        variants_data = json.load(traj_file)

    for v, t_list in variants_data.items():
        for t in t_list:
            trajectory_variant[t.split('.')[0]] = v

    # Get list of all JSON files
    file_paths = []
    for root, _, files in os.walk(data_dir):
        new_files = [os.path.join(root, f) for f in files
                   if f.endswith('.json') and not f.startswith('trajectory_variants')]
        file_paths += new_files
    
    final_variants = dict()

    for f in tqdm(file_paths):
        scenario = f.split('/')[-1].split('_')[0]
        v = trajectory_variant[scenario]
        if v not in final_variants.keys():
            final_variants[v] = {'files':[], 'ratings':[]}
        final_variants[v]['files'].append(f)
        with open(f, 'r') as traj_file:
            trajectory_data = json.load(traj_file)

        final_variants[v]['ratings'].append(trajectory_data['label'])

    stratified_variants = {0.2: [], 0.4:[], 0.6:[], 0.8:[], 1.0:[]}
    ratings = list(stratified_variants.keys())
    for v in final_variants:
        mean_rating = np.mean(np.array(final_variants[v]['ratings']))
        for r in ratings:
            if mean_rating<=r:
                break
        stratified_variants[r].append(v)

    # Create splits
    train_files = []
    val_files = []
    test_files = []

    for r in ratings:
        print(f'number of variants with ratings less than {r}', len(stratified_variants[r]))

        scenarios_list = stratified_variants[r]
        random.shuffle(scenarios_list)

        total_files = len(scenarios_list)
        train_end = int(train_ratio * total_files)
        val_end = train_end + int(val_ratio * total_files)

        # Create splits
        for s in scenarios_list[:train_end]:
            train_files += final_variants[s]['files']

        for s in scenarios_list[train_end:val_end]:
            val_files += final_variants[s]['files']

        for s in scenarios_list[val_end:]:
            test_files += final_variants[s]['files']

    # Write splits to text files
    with open("train_set.txt", "w") as train_file:
        train_file.writelines(f"{path}\n" for path in train_files)

    with open("val_set.txt", "w") as val_file:
        val_file.writelines(f"{path}\n" for path in val_files)

    with open("test_set.txt", "w") as test_file:
        test_file.writelines(f"{path}\n" for path in test_files)

    print(f"Data split complete: {len(train_files)} train, {len(val_files)} validation, and {len(test_files)} test.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Dataset splitter into train, validation and test sets')

    parser.add_argument('--dataset', type=str, nargs='?', required=True, help='Directory containing the labeled dataset')
    parser.add_argument('--trainpercentage', type=int, nargs='?', required=False, default=90, help='Percentage of data in the train set')
    parser.add_argument('--valpercentage', type=int, nargs='?', required=False, default=5, help='Percentage of data in the validation set')
    args = parser.parse_args()

    train_ratio = args.trainpercentage/100.
    val_ratio = args.valpercentage/100.
    if train_ratio+val_ratio>1.:
        print("The percentages of the training and validation sets can not be greater than 100")
        exit()
    test_ratio = 1. - (train_ratio+val_ratio)
    dataset_dir = args.dataset
    data_splitter(dataset_dir, train_ratio, val_ratio, test_ratio)
