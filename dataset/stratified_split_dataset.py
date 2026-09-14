import os
import random
import json
import argparse
import numpy as np
from tqdm import tqdm

def data_splitter(data_dir, train_ratio, val_ratio, ngroups, baseline_test):

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

    baseline_test_variants = []
    if baseline_test!='none':
        with open(baseline_test) as set_file:
            ds_files = set_file.read().splitlines()
            traj_names = [f.split('/')[-1].split('_')[0] for f in ds_files]
        for t in traj_names:
            v = trajectory_variant[t]
            baseline_test_variants.append(v)


    for f in tqdm(file_paths):
        scenario = f.split('/')[-1].split('_')[0]
        v = trajectory_variant[scenario]
        if v not in final_variants.keys():
            final_variants[v] = {'files':[], 'ratings':[]}
        final_variants[v]['files'].append(f)
        with open(f, 'r') as traj_file:
            trajectory_data = json.load(traj_file)

        final_variants[v]['ratings'].append(trajectory_data['label'])

    label_groups = np.linspace(0., 1., ngroups)
    stratified_variants =  {k: [] for k in label_groups}
    assign_to_test_variants =  {k: [] for k in label_groups}
    ratings = list(stratified_variants.keys())
    for v in final_variants:
        mean_rating = np.mean(np.array(final_variants[v]['ratings']))
        for r in ratings:
            if mean_rating<=r:
                break
        if v in baseline_test_variants:
            assign_to_test_variants[r].append(v)
        else:
            stratified_variants[r].append(v)

    # Create splits
    train_files = []
    val_files = []
    test_files = []

    for r in ratings:
        print(f'number of variants with ratings less than {r}', len(stratified_variants[r])+len(assign_to_test_variants[r]))

        scenarios_list = stratified_variants[r]
        assign_to_test = assign_to_test_variants[r]
        random.shuffle(scenarios_list)

        total_files = len(scenarios_list)+len(assign_to_test)

        n_train = round(train_ratio * total_files)
        n_val = round(val_ratio * total_files)
        n_test = total_files - n_train - n_val
        n_baseline_test = len(assign_to_test_variants[r])

        if n_baseline_test>n_test:
            test_excess = n_baseline_test-n_test
            train_excess = test_excess//2
            val_excess = test_excess-train_excess
            n_train = n_train-train_excess
            n_val = n_val-val_excess

        train_end = n_train
        val_end = train_end + n_val


        print(f'number in train {n_train}, number in validation {n_val}, number in test {n_test}, number in baseline_test {n_baseline_test}')


        # Create splits
        for s in scenarios_list[:train_end]:
            train_files += final_variants[s]['files']

        for s in scenarios_list[train_end:val_end]:
            val_files += final_variants[s]['files']

        for s in scenarios_list[val_end:]:
            test_files += final_variants[s]['files']

        for s in assign_to_test:
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
    parser.add_argument('--ngroups', type=int, required=False, default=5, help='Number of groups for label distribution')
    parser.add_argument('--baseline_test', type=str, default='none', help='Path to the baseline test subset')
    args = parser.parse_args()

    train_ratio = args.trainpercentage/100.
    val_ratio = args.valpercentage/100.
    if train_ratio+val_ratio>1.:
        print("The percentages of the training and validation sets can not be greater than 100")
        exit()
    test_ratio = 1. - (train_ratio+val_ratio)
    dataset_dir = args.dataset
    ngroups = args.ngroups
    baseline_test = args.baseline_test
    data_splitter(dataset_dir, train_ratio, val_ratio, ngroups, baseline_test)
