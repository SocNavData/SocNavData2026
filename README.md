# SocNavData2026 dataset code and tools

Official repository of the paper [Towards Data-Driven Metrics for Social Robot Navigation Benchmarking](https://arxiv.org/abs/2509.01251)

This project is a joined effort towards the development of a data-driven Social Robot Navigation metric to facilitate benchmarking and policy optimization. Motivated by the lack of a standardized method to benchmark Social robot Navigation (SocNav) policies, we propose an **A**ll-encompassing **L**earned **T**rajectory-wise (ALT) metric, which is learned directly from human evaluations of full robot trajectories, conditioned on goals and contexts.

This repository contains the core code and utilities for working with the proposed dataset (SocNavData2026). Alongside a baseline implementation to replicate our results, it also includes tools to check and visualize data, supporting dataset extension and further research.

All data required to run the code is available at the following link: [SocNavData2026_all_data](https://www.dropbox.com/scl/fo/5mdx98kxux31tpz17t737/ABZuqYOXVMrcGJmUGeBQBo0?rlkey=70f89t67bg4zoa6g6lw5dcflg&st=2o6n9lbn&dl=0)

🚀 Do you want to **test the metric live**? Check it out at [https://socnavdata.github.io/SocNavData2026/](https://socnavdata.github.io/SocNavData2026/)! It will take you to a simple web-based simulator where the robot uses a social force model to move. You can define new scenarios and test what the metric would output (it will take **a few seconds to load**!). 

📺 We also have a [video introduction](https://socnavdata.github.io/SocNavData2026/sn26_intro.mp4) to the motivations, aims, and results of our work:
<div><a href="https://socnavdata.github.io/SocNavData2026/sn26_intro.mp4"><img src="https://socnavdata.github.io/SocNavData2026/thumb.png" alg="link to intro video" /></a></div>


## Dataset

The dataset comprises variables related to raters, trajectories, and rater-trajectory scores. For every rater, together with demographic information, a rating list is stored. The rating list contains tuples (_t_, _c_, _r_), where _t_ is a trajectory identiﬁer (string), _c_ is a context (string), and _r_ is a score assigned by the rater to the trajectory _t_ given the context _c_.

Trajectories contain data on the robot, the task and its context, humans, objects, and the environment. Except for variables related to the task and the environment, which apply to the whole trajectory, variables are recorded with a timestamp at each time step. Next section includes a description of the data stored per trajectory.

Contexts are textual descriptions of the specific situations that occur during the trajectory. They are not necessarily bound to trajectories when trajectories are recorded; this enables us to vary the context to explore how different contexts affect the perception of the same trajectory.

### Data format

The following table summarizes the data stored per trajectory.
A JSON schema with the required structure can also be found at _dataset/check_trajectory_format/schema.json_. Additionally, trajectory files can be validated using the tool _dataset/check_trajectory_format/checkjson.py_.

| **Type**       | **Variable**            | **Description** |
|----------------|-------------------------|-----------------|
| **Robot**      | Pose                    | 2D position (m) and orientation (rad) on the plane. |
|                | Speed                   | Lineal (m/s), angular (rad/s). |
|                | Drive                   | Categorical (differential / omni / ackerman). |
|                | Shape                   | 2D *circle* (radius), *rectangle* (width, height), or *polygon* (list of points). |
| **Task**       | Type                    | Task type, either *“go-to”*, *“guide-to”* or *“follow”* $^*$. |
|                | Position + threshold    | For go-to and guide-to tasks. 2D position + threshold (m). |
|                | Orientation + threshold | For go-to and guide-to tasks. Orientation + threshold (rad). |
|                | Human identifier        | For *guide-to* and *follow* tasks. |
|                | Context                 | Textual description of the context, in English. |
| **Humans**     | Identifier              | Integer that uniquely identifies the human in a given episode. |
|                | Pose                    | 2D position (m) and orientation (rad) on the plane. |
|                | Full Pose (optional)    | The 3D position of the COCO-18 key point set. |
| **Objects**    | Identifier              | Integer that uniquely identifies the object in a given episode. |
|                | Type                    | Free text describing the type of the object. |
|                | Pose                    | 2D position (m) and orientation (rad) on the plane. |
|                | Shape                   | The 2D shape of the object. |
| **Environment**| Walls                   | Sequence of polylines (2D, m). |
|                | Grid                    | Occupancy map: 2D grid + resolution (m/cell). |
|                | Area semantics          | Free text describing the area, e.g., “indoor”, “outdoor”, “kitchen”, “a science museum”. |

$^*$ The current version of the dataset (as of 2025-08-25), contains *“go-to”* trajectories exclusively  .

### Data organization

The raw dataset contains two main directories: one containing the trajectories and another one containing data about the raters and their ratings. 

The trajectories directory contains JSON ﬁles of recorded trajectories in sub-directories named according to the source of the trajectory data. Each ﬁle contains one trajectory with the structure described in the previous section. There is an additional file (_trajectory_variants.json_) that groups together all the variants of each trajectory (e.g., corresponding to the same scenario with different walls' configurations).

The ratings directory contains a separate JSON ﬁle for each rater. The rating list includes control questions that allow analyzing the consistency of the data.

The raw trajectories' dataset can be found at [SocNavData2026_all_data/dataset/unlabeled](https://www.dropbox.com/scl/fo/ze7op896sqb5tog89xnpl/AEm4g0fbyV_71tpR1ESH7Ic?rlkey=ev768vt29mug8b6z2acg3fdjf&st=dce05pti&dl=0). The ratings are available at [SocNavData2026_all_data/ratings](https://www.dropbox.com/scl/fo/yybho991ousbt1grhnd1s/ABwXfRZpGrIQ_Tx8RK9XUBM?rlkey=nok46jegkd3xsobdwdwhhxygd&st=669o74cw&dl=0). This last folder contains all the ratings and a selected set of ratings resulting from a consistency analysis.

After downloading trajectories and ratings, a labeled dataset can be obtained by running the following commands:

```bash
cd dataset
python3 label_dataset.py --trajectories PATH_TO_THE_TRAJECTORIES_DIRECTORY --ratings PATH_TO_THE_RATINGS_DIRECTORY
```

The process creates two directories with the labeled trajectories, one including the control trajectories and another one with the remaining trajectories.

A labeled version of the dataset can be directly downloaded from [SocNavData2026_all_data/dataset/labeled](https://www.dropbox.com/scl/fo/v4432r635kciu8x7eq093/AGFbMkKcJw3MpL8ff92flcs?rlkey=w4hnhzpduzkx0d44aoh2flbkp&st=9kf775q6&dl=0).

Once the labeled dataset is generated, it can be used for training a model producing an ALT-metric. For that, the whole dataset can be split into train/validation/test sets using the script dataset/split_dataset.py as follows:

```bash
cd dataset
python3 split_dataset.py --dataset PATH_TO_THE_LABELED_DATASET
```
The default split is 0.9/0.05/0.05. It can be modified using the arguments _--trainpercentage_ and _--valpercentage_.

The split used in our experiments is available at [SocNavData2026_all_data/dataset/split](https://www.dropbox.com/scl/fo/6r83hv5pvrxhqs43692eb/AKak5wV8neRBl_O5--Tzayc?rlkey=2oujnu64d2jkigz6647y0vz8k&st=xhcqwg5g&dl=0).

## Tools

The repository includes several tools for data analysis,  transformation and visualization.

### Data analysis

The data analysis tools enable the determination of rating quality and the selection of a subset of valid ratings. The tool _tools/data_analysis/check_quality.py_ displays information about the consistency of the raters, given a ratings directory, and produces a consistency map showing both inter- and intra-rater consistency. It can be run with the following commands:

```bash
cd tools/data_analysis
python3 check_quality.py --ratings_dir PATH_TO_THE_RATINGS_DIRECTORY
```

According to the consistency analysis, a subset of valid raters can be obtained using _select_valid_raters.py_ as follows:

```bash
cd tools/data_analysis
python3 select_valid_raters.py --ratings_dir PATH_TO_THE_RATINGS_DIRECTORY --output_dir OUTPUT_DIRECTORY
```
### Data transformation

The sequence in a trajectory can be transformed for data normalization and augmentation purposes. The directory _tools/data_transformation_ includes several transformation utilities with the following functionality:

* **data_mirroring.py**: applies a mirroring transformation to a trajectory.
* **data_normalization.py**: reframes all poses of a trajectory into the goal frame of reference.
* **data_random_noise.py**: adds random noise to the poses of each scenario entity for augmentation.
* **data_random_orientation.py**: applies random orientation changes for augmentation.
* **transforms.py**: defines a PyTorch transform for each transformation.

### Data visualization

Trajectories can be visualized for checking the correctness of the data they include. The tool _tools/data_visualization/view_data.py_ generates a 2D top view of the scenario and the robot trajectory given the corresponding JSON file. It can be run with the following commands:

```bash
cd tools/data_visualization
python3 view_data.py TRAJECTORY_FILE --videowidth VIEW_WIDTH --videoheight VIEW_HEIGHT
```
Different arguments can be used to adjust the view and, optionally, generate a video.

A 3D visualization tool built on top of Webots is
also provided in _tools/video_generator_. This tool produces a video recording for each trajectory, showing a 3D top view of the scenario. This is the tool we used to generate the videos shown to the raters in the survey.


## Baseline

The SocNavData2026 dataset has been used to train an RNN-based ALT metric model. The code to train and test the model is available in the _baseline_ subdirectory.

### Model training

Before training a model, the labeled dataset has to be split into train/validation/test sets as explained in section [Dataset](#dataset). Each trajectory in these sets is converted into a sequence of 1-D vectors that is used as input of the RNN. These vectors include trajectory features, metric-based features and an ad-hoc context embedding.

The context embeddings are generated using queries to a large language model (LLM), which converts each context description into numerical representations. These embeddings capture variables related to factors such as task urgency, risk, and importance. The quantization of these variables is pre-computed and stored in CSV files. We provide four different quantization files (available at [SocNavData2026_all_data/contexts](https://www.dropbox.com/scl/fo/5t8b6an13kge3a9sbw8eg/AM1GltxDRaYpsbi0jtn91E4?rlkey=s9ybki84pq56xnopler2m9ryw&st=x42myq1y&dl=0)), each corresponding to the outputs of a different LLM.

The model's hyperparameters are specified in a YAML file. Among other parameters related with the model architecture, the number of epochs, the batch size, etc., it includes the dataset split (TXT files containing the paths of the labeled trajectories for training, validation and testing) and the context quantization file (i.e., CSV file containing the context embeddings produced by a specific LLM). The file _baseline/train.yaml_ shows an example of such configuration. The training can be started with:

```bash
cd baseline
python3 train.py --task YAML_TRAINING_CONFIGURATION_FILE
```

A baseline model trained using this procedure can be found at [SocNavData2026_all_data/models/](https://www.dropbox.com/scl/fo/h3lyxk9w2udsirlt8on07/AKFbx5CEj3v_xvCEOnj43Xc?rlkey=p59252o25250gx3xqlflcclp4&st=24yhuhq4&dl=0).

During execution, the training process displays progress information, including the training and validation loss, the current epoch, and loss improvements. Additionally, it generates two types of plots:

* A plot comparing the expected versus predicted outputs on the test set.

* A plot showing qualitative results across several sets of trajectories for different contexts.

For the second plot, the sets of trajectories and contexts must be specified in a separate YAML configuration file. The path to this file is then referenced in the main training configuration file. We provide sample files for this qualitative evaluation at [SocNavData2026_all_data/qualitative_tests](https://www.dropbox.com/scl/fo/nyiz9bxxzypefqkdtob75/AJ53hAofJODob--WEi9JUAA?rlkey=at05w27lh3vmo7k2fwgsuap3f&st=7wboebcj&dl=0). The qualitative test can also be run separately using a dedicated script, as explained in the next section.


### Model evaluation

We provide scripts to evaluate a trained model:

* _evaluate_model.py_ : Generates score predictions for the specified labeled test set using a trained model and prints the Mean Squared Error (MSE) and Mean Absolute Error (MAE). Run the script with:

```bash
cd baseline
python3 evaluate_model.py --model MODEL_FILE --dataset TEST_SET_FILE --dataroot MAIN_DIRECTORY_OF_THE_TEST_SET_FILE --context CONTEXT_QUANTIZATION_FILE
```

* _control_results.py_ : Compares the predictions produced by the specified model on the control questions and prints statistics summarizing the comparison. Additionally, it generates a plot showing the mean and standard deviation of the control questions and the model's estimations. Run the script with:

```bash
cd baseline
python3 control_results.py --model MODEL_FILE --control_path DIRECTORY_WITH_THE_CONTROL_LABELED_TRAJECTORIES --context CONTEXT_QUANTIZATION_FILE
```

* _plot_qual_with_contexts.py_ : Generates (and, optionally, saves) qualitative plots for specific sets of trajectories and contexts. Both the trajectories and contexts must be specified in a configuration file, which is passed as an argument to the script. Each trajectory set is assumed to correspond to the same scenario but with different robot trajectories. Sample qualitative test sets and configuration files can be downloaded from [SocNavData2026_all_data/qualitative_tests](https://www.dropbox.com/scl/fo/nyiz9bxxzypefqkdtob75/AJ53hAofJODob--WEi9JUAA?rlkey=at05w27lh3vmo7k2fwgsuap3f&st=7wboebcj&dl=0). Run the script with:  

```bash
cd baseline
python3 plot_qual_with_context.py --model MODEL_FILE --config QUALITATIVE_TEST_CONFIG_FILE --dataroot MAIN_DIRECTORY_OF_THE_TRAJECTORY_FILES --context CONTEXT_QUANTIZATION_FILE
```

## How to Contribute

We encourage the community to help **scale the dataset** by contributing **new trajectories** and **ratings**. A sufficiently large and diverse dataset extension will enable the development of a consistent and reliable **data-driven SocNav metric** that benefits the entire community.

### **Contributing New Trajectories**

To contribute with new trajectories:  

1. **Record your data** according to the format described in section [Data format](#data-format).  
2. **Validate each trajectory file** using the tool _checkjson.py_:  
   ```bash
   cd dataset/check_trajectory_format
   python3 checkjson.py TRAJECTORY_FILES
   ```
3. **Visualize trajectories** to ensure that coordinate and unit systems are correct using the tool _view_data.py_:

   ```bash
    cd tools/data_visualization
    python3 view_data.py TRAJECTORY_FILE --videowidth VIEW_WIDTH --videoheight VIEW_HEIGHT
    ```
4. **Contact us** to share your trajectories: 
 * Luis J. Manso: l.manso@aston.ac.uk 
 * Pilar Bachiller-Burgos: pilarb@unex.es

If you struggle to validate your data, we can help you run the validation checks.

Once validated, we will add your trajectories to the dataset and include your name/organization in the list of SocNavData2026 contributors.

### **Contributing New Ratings**

To contribute with new ratings, use our [Survey Tool](https://survey.socnav3.com).
You'll find detailed instructions there to guide you through the steps required to complete the rating process. The survey is completely anonymous.

## Data contributors
The following are the current contributors of robot trajectories:
* **Pilar Bachiller** (Simulated data acquired using [SocNavGym](https://github.com/gnns4hri/SocNavGym/)) -- Universidad de Extremadura
* **Luis J. Manso** (Real data using an RB-1 robot at Aston University) -- Aston University
* **Phani T. Singamaneni** (Simulated data on Gazebo) -- Laboratory for Analysis and Architecture of Systems - CNRS
* **No&eacute; P&eacute;rez** (Simulated data on Gazebo) -- Universidad Pablo de Olavide
* **Noriaki Hirose** and **Dhruv Shah** (Adaptation of data from the SACSoN dataset) -- Toyota, UC Berkeley, Google DeepMind
