---
layout: page
permalink: /drivaerml/
title: DrivAerML
description: 
nav: false
nav_order: 2
---

<h3>Summary</h3>
---------
Machine Learning (ML) has the potential to revolutionise the field of automotive aerodynamics, enabling split-second flow predictions early in the design process.
However, the lack of open-source training data for realistic road cars, using high-fidelity CFD methods, represents a barrier to their development.
To address this, a high-fidelity open-source (CC-BY-SA) public dataset for automotive aerodynamics has been generated, based on 500 parametrically morphed variants of the widely-used DrivAer notchback generic vehicle. Mesh generation and scale-resolving CFD was executed using consistent and validated automatic workflows representative of the industrial state-of-the-art. Geometries and rich aerodynamic data are published in open-source formats. To our knowledge, this is the first large, public-domain dataset for complex automotive configurations generated using high-fidelity CFD.

<img class="photo" alt="drivaer" src="{{ site.baseurl }}/assets/img/drivaer1.png">
<h3>CFD Solver:</h3>
----------
All cases were run using the open-source finite-volume code OpenFOAM v2212 with custom modifications by UpstreamCFD. Please see the paper below for full details on the code and validation:

<h3>How to cite this dataset:</h3>
----------------
In order to cite the use of this dataset please cite the paper below which contains full details on the dataset.It can be found [here](https://arxiv.org/abs/2408.11969)
```
@article{ashton2024drivaer,
    title = {DrivAerML: High-Fidelity Computational Fluid Dynamics Dataset for Road-Car External Aerodynamics},
    year = {2024},
    journal = {arxiv.org},
    url={https://arxiv.org/abs/2408.11969},
    author = {Ashton, N., Mockett, C., Fuchs, M., Fliessbach, L., Hetmann, H., Knacke, T., Schonwald, N.,
Skaperdas, V., Fotiadis, G., Walle, A., Hupertz, B., and Maddix, D}
}
```
<h3>How to download:</h3>
----------------

There are currently two routes to download the data - with the long-term focus being on HuggingFace:

Option 1: HuggingFace
--------------
Please note you'll need to have git lfs installed first, then you can run the following command:
```
git clone git@hf.co:datasets/neashton/drivaerml
```
Option 2: AWS
--------

Please ensure you have enough local disk space before downloading (complete dataset is 30TB) and consider the examples below that provide ways to download just the files you need:

<h5>First Step: Install AWS Command Line Interface (CLI):</h5>
--------------

Follow instructions here: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

<h5>Second Step: Use the AWS CLI to download the dataset</h5>
--------------
Follow the following examples for how to download all or part of the dataset.

Note 1 : If you don't have an AWS account you will need to add --no-sign-request within your AWS command i.e aws s3 cp --no-sign-request --recursive etc...

Note 2 : If you have an AWS account, please note the bucket is in us-east-1, so you will have the fastest download if you have your AWS service or EC2 instance running in us-east-1.

<h5>Example 1: Download all files (~30TB)</h5>
-------------------------
```
aws s3 cp --recursive s3://caemldatasets/drivaer/dataset .
```
<h5>Example 2: only download select files (e.g STL,images & force and moments):</h5>
---------------------
Create the following bash script that could be adapted to loop through only select runs or to change to download different files e.g boundary/volume.

```
#!/bin/bash

# Set the S3 bucket and prefix
S3_BUCKET="caemldatasets"
S3_PREFIX="drivaer/dataset"

# Set the local directory to download the files
LOCAL_DIR="./drivaer_data"

# Create the local directory if it doesn't exist
mkdir -p "$LOCAL_DIR"

# Loop through the run folders from 1 to 500 (here you can change the number to only download a subset of the runs)
for i in $(seq 1 500); do
    RUN_DIR="run_$i"
    RUN_LOCAL_DIR="$LOCAL_DIR/$RUN_DIR"

    # Create the run directory if it doesn't exist
    mkdir -p "$RUN_LOCAL_DIR"

    # Download the drivaer_i.stl file
    aws s3 cp "s3://$S3_BUCKET/$S3_PREFIX/$RUN_DIR/drivaer_$i.stl" "$RUN_LOCAL_DIR/" --only-show-errors

    # Download the force_mom_i.csv file
    aws s3 cp "s3://$S3_BUCKET/$S3_PREFIX/$RUN_DIR/force_mom_$i.csv" "$RUN_LOCAL_DIR/" --only-show-errors

    aws s3 cp --recursive "s3://$S3_BUCKET/$S3_PREFIX/$RUN_DIR/images" "$RUN_LOCAL_DIR/images/" --only-show-errors
done
```

<h3>Files:</h3>
-------
Each folder (e.g run1,run2...run"i" etc) corresponds to a different geometry that contains the following files where "i" is the run number:
* drivaer_i.stl: geometry stl (~135mb)
* geo_ref_i.csv: reference values for each geometry
* geo_parameters_i.csv: reference geometry for each geometry
* boundary_i.vtp: Boundary VTP (~500mb)
* volume_i.vtu: Volume field VTU (~25GB)
* force_mom_i.csv: forces/moments time-averaged (using varying frontal area/wheelbase)
* force_mom_constref_i.csv: forces/moments time-averaged (using constant frontal area/wheelbase)
* slices: folder containing .vtp slices in x,y,z that contain flow-field variables
* Images: This folder contains images of various flow variables (e.g. Cp, CpT, UMagNorm) for slices of the domain at X, Y, and Z locations (M signifies minus, P signifies positive), as well as on the surface. It also includes evaluation plots of the time-averaging of the force coefficients (via the tool MeanCalc) and a residual plot illustrating the convergence.

<h3>Acknowledgements</h3>
-----

* CFD solver and workflow development by Charles Mockett, Marian Fuchs, Louis Fliessbach, Henrik Hetmann, Thilo Knacke & Norbert Schonwald (UpstreamCFD)
* Geometry parameterization by Vangelis Skaperdas, Grigoris Fotiadis (BETA-CAE Systems) & Astrid Walle (Siemens Energy)
* Meshing development workflow by Vangelis Skaperdas & Grigoris Fotiadis (BETA-CAE Systems)
* DrivAer advise and consultation by Burkhard Hupertz (Ford)
* Guidance on dataset preparation for ML by Danielle Maddix (Amazon Web Services)
* Simulation runs, HPC setup and dataset preparation by Neil Ashton (Amazon Web Services)

<h3>License</h3>
----
This dataset is provided under the CC BY SA 4.0 license, please see LICENSE.txt for full license text.
