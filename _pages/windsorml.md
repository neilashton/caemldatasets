---
layout: page
permalink: /windsorml/
title: WindsorML
description: 
nav: false
nav_order: 2
---

<h3>Summary</h3>
-----------
This work presents a new open-source high-fidelity dataset for Machine Learning (ML) containing 355 geometric variants of the Windsor body, to help the development and testing of ML surrogate models for external automotive aerodynamics. Each Computational Fluid Dynamics (CFD) simulation was run with a GPU-native high-fidelity Wall-Modeled Large-Eddy Simulations (WMLES) using a Cartesian immersed-boundary method using more than 280M cells to ensure the greatest possible accuracy. The dataset contains geometry variants that exhibits a wide range of flow characteristics that are representative of those observed on road-cars.
The dataset itself contains the 3D time-averaged volume & boundary data as well as the geometry and force & moment coefficients. This paper discusses the validation of the underlying CFD methods as well as contents and structure of the dataset. To the authors knowledge, this represents the first, large-scale high-fidelity CFD dataset for the Windsor body with a permissive open-source license (CC-BY-SA).

<img class="photo" alt="windsor" src="{{ site.baseurl }}/assets/img/case1_param_description.png">
<h3>CFD Solver</h3>
-----------
All cases were run using the Volcano Platforms commerical CFD solver, which is based upon a GPU-native cartesian immersed-boundary method Wall-Modelled Large-Eddy Simulation (WMLES) approach. Each case was run transiently for approximately 80 convective time units (CTU) on meshes of approximately 300M cells.  Please see the paper for full details on the code and validation:

<h3>How to cite this dataset</h3>
-----------
In order to cite the use of this dataset please cite the paper below which contains full details on the dataset. It can be found [here](https://arxiv.org/abs/2407.19320)

```
@article{ashton2024windsor,
    title = {WindsorML: High-Fidelity Computational Fluid Dynamics dataset for automotive aerodynamics},
    year = {2024},
    journal = {arxiv.org},
    url={https://arxiv.org/abs/2407.19320},
    author = {Ashton, Neil and Angel, Jordan and Ghate, Aditya and Kenway, Gaetan and Long Wong, Man and Kiris, Cetin and Walle, Astrid and Maddix, Danielle and Page, Gary}
}
```

<h3>How to download</h3>
-------------
Please ensure you have enough local disk space before downloading (complete dataset is 8TB) and consider the examples below that provide ways to download just the files you need:

<h5>First Step: Install AWS Command Line Interface (CLI):</h5>
------------
Follow instructions here: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

<h5>Second Step: Use the AWS CLI to download the dataset</h5>
------------
Follow the following examples for how to download all or part of the dataset.

Note 1 : If you don't have an AWS account you will need to add --no-sign-request within your AWS command i.e aws s3 cp --no-sign-request --recursive etc...
Note 2 : If you have an AWS account, please note the bucket is in us-east-1, so you will have the fastest download if you have your AWS service or EC2 instance running in us-east-1.

<h5>Example 1: Download all files (~8TB)</h5>
---------
```
aws s3 cp --recursive s3://caemldatasets/windsor/dataset .
```
<h5>Example 2: only download select files (e.g STL,images & force and moments):</h5>
-------------
Create the following bash script that could be adapted to loop through only select runs or to change to download different files e.g boundary/volume.

```
#!/bin/bash

# Set the S3 bucket and prefix
S3_BUCKET="caemldatasets"
S3_PREFIX="windsor/dataset"

# Set the local directory to download the files
LOCAL_DIR="./windsor_data"

# Create the local directory if it doesn't exist
mkdir -p "$LOCAL_DIR"

# Loop through the run folders from 0 to 354 (here you can change the number to only download a subset of the runs)
for i in $(seq 0 354); do
    RUN_DIR="run_$i"
    RUN_LOCAL_DIR="$LOCAL_DIR/$RUN_DIR"

    # Create the run directory if it doesn't exist
    mkdir -p "$RUN_LOCAL_DIR"

    # Download the windsor_i.stl file
    aws s3 cp "s3://$S3_BUCKET/$S3_PREFIX/$RUN_DIR/windsor_$i.stl" "$RUN_LOCAL_DIR/" --only-show-errors

    # Download the force_mom_i.csv file
    aws s3 cp "s3://$S3_BUCKET/$S3_PREFIX/$RUN_DIR/force_mom_$i.csv" "$RUN_LOCAL_DIR/" --only-show-errors

    aws s3 cp --recursive "s3://$S3_BUCKET/$S3_PREFIX/$RUN_DIR/images" "$RUN_LOCAL_DIR/images/" --only-show-errors
done
```
<h3>Files:</h3>
-------
Each folder (e.g run_1,run_2...run_"i" etc) corresponds to a different geometry that contains the following files where "i" is the run number:
windsor_i.stl : geometry stl (~5mb)
windsor_i.stp : geometry step (~1mb)
geo_parameters_1.csv : parameters that define the geometry (explained in the associated paper)
boundary_i.vtu : Boundary VTU (~500mb)
volume_i.vtu : Volume field VTU (~20GB)
force_mom_i.csv : forces/moments time-averaged (Cd,Cs,Cl,Cmy)
force_mom_varref_i.csv: forces/moments time-averaged (Cd,Cs,Cl,Cmy) using unique reference area per geometry
images (folder) that contains images of the following variables (pressure, velocityX,ReynoldsStressXX,YY,ZZ) for slices of the domain in the X,Y & Z locations as well as an image of the geometry itself (windsor_i.png)
force_mom_all.csv: contains force/moments for all runs in a single file
force_mom_varref_all.csv: contains force/moments for all runs in a single file using a reference frontal area that is unique to each geometry
geo_parameters_all.csv: contains all the geometry parameters for all the runs in a single file

<h3>Acknowledgements</h3>
-----------
* CFD solver and workflow development by Jordan Angel, Aditya Ghate, Gaetan Kenway, Man Long Wong, Cetin Kiris (Volcano Platforms) and Neil Ashton (Amazon Web Services)
* Geometry parameterization by Astrid Walle (Siemens Energy)
* Windsor advise and consultation by Gary Page (Loughborough University)
* Guidance on dataset preparation for ML by Danielle Maddix (Amazon Web Services)
* Simulation runs, HPC setup and dataset preparation by Neil Ashton (Amazon Web Services)

<h3>License</h3>
-----------
This dataset is provided under the CC BY SA 4.0 license, please see LICENSE.txt for full license text.
