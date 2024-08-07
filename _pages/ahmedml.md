---
layout: page
permalink: /ahmedml/
title: AhmedML
description: 
nav: false
nav_order: 2
---

<h3>Summary</h3>
------
The development of Machine Learning (ML) methods for Computational Fluid Dynamics (CFD) is currently limited by the lack of openly available training data. This work presents a new open-source dataset comprising of high fidelity, scale-resolving CFD simulations of 500 geometric variations of the Ahmed Car Body - a simplified car-like shape that exhibits many of the flow topologies that are present on bluff bodies such as road vehicles. The dataset contains simulation results that exhibit a broad set of fundamental flow physics such as geometry and pressure-induced flow separation as well as 3D vortical structures. Each variation of the Ahmed car body were run using a high-fidelity, time-accurate, hybrid Reynolds-Averaged Navier-Stokes (RANS) - Large-Eddy Simulation (LES) turbulence modelling approach using the open-source CFD code OpenFOAM. The dataset contains boundary, volume, geometry, and time-averaged forces/moments in widely used open-source formats. In addition, the OpenFOAM case setup is provided so that others can reproduce or extend the dataset. This represents to the authors knowledge, the first open-source large-scale dataset using high-fidelity CFD methods for the widely used Ahmed car body that is available to freely download with a permissive license (CC-BY-SA).

<img class="photo" alt="ahmed" src="{{ site.baseurl }}/assets/img/ahmed_body.png">

<h3>CFD Solver</h3>
-------
All cases were run using the open-source finite-volume code OpenFOAM v2212. Each case was run transiently for approximately 80 convective time units (CTU) on meshes of approximately 20M cells.  Please see the paper for full details on the code and validation:

<h3>How to cite this dataset:</h3>
----------
In order to cite the use of this dataset please cite the paper below which contains full details on the dataset. You can download the paper [here](https://arxiv.org/abs/2407.20801)
```
@article{ashton2024ahmed,
    title = {AhmedML: High-Fidelity Computational Fluid Dynamics Dataset for Incompressible, Low-Speed Bluff Body Aerodynamics},
    year = {2024},
    journal = {arxiv.org},
    author = {Ashton, Neil and Maddix, Danielle and Gundry, Samuel and Shabestari, Parisa},
    url={https://arxiv.org/abs/2407.20801},
    abstract={The development of Machine Learning (ML) methods for Computational Fluid Dynamics (CFD) is currently limited by the lack of openly available training data. This paper presents a new open-source dataset comprising of high fidelity, scale-resolving CFD simulations of 500 geometric variations of the Ahmed Car Body - a simplified car-like shape that exhibits many of the flow topologies that are present on bluff bodies such as road vehicles. The dataset contains simulation results that exhibit a broad set of fundamental flow physics such as geometry and pressure-induced flow separation as well as 3D vortical structures. Each variation of the Ahmed car body were run using a high-fidelity, time-accurate, hybrid Reynolds-Averaged Navier-Stokes (RANS) - Large-Eddy Simulation (LES) turbulence modelling approach using the open-source CFD code OpenFOAM. The dataset contains boundary, volume, geometry, and time-averaged forces/moments in widely used open-source formats. In addition, the OpenFOAM case setup is provided so that others can reproduce or extend the dataset. This represents to the authors knowledge, the first open-source large-scale dataset using high-fidelity CFD methods for the widely used Ahmed car body that is available to freely download with a permissive license (CC-BY-SA).},
}
```
<h3>How to download:</h3>
-----------
Please ensure you have enough local disk space before downloading (complete dataset is 2TB) and consider the examples below that provide ways to download just the files you need:

<h5>First Step: Install AWS Command Line Interface (CLI):</h5>
--------------

Follow instructions here: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

<h5>Second Step: Use the AWS CLI to download the dataset</h5>
--------------
Follow the following examples for how to download all or part of the dataset.

Note 1 : If you don't have an AWS account you will need to add --no-sign-request within your AWS command i.e aws s3 cp --no-sign-request --recursive etc...

Note 2 : If you have an AWS account, please note the bucket is in us-east-1, so you will have the fastest download if you have your AWS service or EC2 instance running in us-east-1.

<h5>Example 1: Download all files (~2TB)</h5>
--------
```
aws s3 cp --recursive s3://caemldatasets/ahmed/dataset .
```
<h5>Example 2: only download select files (STL,images & force and moments):</h5>
---------
Create the following bash script that could be adapted to loop through only select runs or to change to download different files e.g boundary/volume.
```
#!/bin/bash

# Set the S3 bucket and prefix
S3_BUCKET="caemldatasets"
S3_PREFIX="ahmed/dataset"

# Set the local directory to download the files
LOCAL_DIR="./ahmed_data"

# Create the local directory if it doesn't exist
mkdir -p "$LOCAL_DIR"

# Loop through the run folders from 1 to 500
for i in $(seq 1 500); do
    RUN_DIR="run_$i"
    RUN_LOCAL_DIR="$LOCAL_DIR/$RUN_DIR"

    # Create the run directory if it doesn't exist
    mkdir -p "$RUN_LOCAL_DIR"

    # Download the ahmed_i.stl file
    aws s3 cp "s3://$S3_BUCKET/$S3_PREFIX/$RUN_DIR/ahmed_$i.stl" "$RUN_LOCAL_DIR/" --only-show-errors

    # Download the force_mom_i.csv file
    aws s3 cp "s3://$S3_BUCKET/$S3_PREFIX/$RUN_DIR/force_mom_$i.csv" "$RUN_LOCAL_DIR/" --only-show-errors

    aws s3 cp --recursive "s3://$S3_BUCKET/$S3_PREFIX/$RUN_DIR/images" "$RUN_LOCAL_DIR/images/" --only-show-errors
done
```

<h3>Acknowledgements </h3>
---------
* OpenFOAM solver and workflow development by Neil Ashton (Amazon Web Services)
* Geometry parameterization by Samuel Gundry (Amazon Web Services) and Parisa Shabestari (Amazon Web Services)
* Guidance on dataset preparation for ML by Danielle Madix (Amazon Web Services)
* Simulation runs, HPC setup and dataset preparation by Neil Ashton (Amazon Web Services)

<h3> License </h3>
--------
This dataset is provided under the CC BY SA 4.0 license, please see LICENSE.txt within the dataset for full license text
