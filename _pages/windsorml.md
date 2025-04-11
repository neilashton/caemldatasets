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
In order to cite the use of this dataset please cite the paper below which contains full details on the dataset. It can be found [here](https://proceedings.neurips.cc/paper_files/paper/2024/hash/42a59a5f35b1b3c3fd648397c88a7164-Abstract-Datasets_and_Benchmarks_Track.html)

```
@article{ashton2024windsor,
    title = {WindsorML: High-Fidelity Computational Fluid Dynamics dataset for automotive aerodynamics},
    year = {2024},
    journal = {Advances in Neural Information Processing Systems 37},
    url={https://proceedings.neurips.cc/paper_files/paper/2024/hash/42a59a5f35b1b3c3fd648397c88a7164-Abstract-Datasets_and_Benchmarks_Track.html},
    author = {Ashton, Neil and Angel, Jordan and Ghate, Aditya and Kenway, Gaetan and Long Wong, Man and Kiris, Cetin and Walle, Astrid and Maddix, Danielle and Page, Gary}
}
```

<h3>How to download</h3>
-------------

The dataset is now available on HuggingFace. Below are some examples of how to download all or selected parts of the dataset. Please refer to the HuggingFace documentation for other ways to accessing the dataset and building workflows.

<h5>Example 1: Download all files (~8TB)</h5>
--------
Please note you'll need to have git lfs installed first, then you can run the following command:

```
git clone git@hf.co:datasets/neashton/windsorml
```

<h5>Example 2: only download select files (STL,images & force and moments):</h5>
---------
Create the following bash script that could be adapted to loop through only select runs or to change to download different files e.g boundary/volume.
```
#!/bin/bash

# Set the path and prefix
HF_OWNER="neashton"
HF_PREFIX="windsorml"

# Set the local directory to download the files
LOCAL_DIR="./windsor_data"

# Create the local directory if it doesn't exist
mkdir -p "$LOCAL_DIR"

# Loop through the run folders from 1 to 500
for i in $(seq 1 354); do
    RUN_DIR="run_$i"
    RUN_LOCAL_DIR="$LOCAL_DIR/$RUN_DIR"

    # Create the run directory if it doesn't exist
    mkdir -p "$RUN_LOCAL_DIR"

    # Download the windsor_i.stl file
    wget "https://huggingface.co/datasets/${HF_OWNER}/${HF_PREFIX}/resolve/main/$RUN_DIR/windsor_$i.stl" -O "$RUN_LOCAL_DIR/windsor_$i.stl"

    # Download the force_mom_i.csv file
    wget "https://huggingface.co/datasets/${HF_OWNER}/${HF_PREFIX}/resolve/main/$RUN_DIR/force_mom_$i.csv" -O "$RUN_LOCAL_DIR/force_mom_$i.csv"

done
```

<h3>Files:</h3>
-------
Each folder (e.g run_1,run_2...run_"i" etc) corresponds to a different geometry that contains the following files where "i" is the run number:
* windsor_i.stl : geometry stl (~5mb)
* windsor_i.stp : geometry step (~1mb)
* geo_parameters_1.csv : parameters that define the geometry (explained in the associated paper)
* boundary_i.vtu : Boundary VTU (~500mb)
* volume_i.vtu : Volume field VTU (~20GB)
* force_mom_i.csv : forces/moments time-averaged (Cd,Cs,Cl,Cmy)
* force_mom_varref_i.csv: forces/moments time-averaged (Cd,Cs,Cl,Cmy) using unique reference area per geometry
* images (folder) that contains images of the following variables (pressure, velocityX,ReynoldsStressXX,YY,ZZ) for slices of the domain in the X,Y & Z locations as well as an image of the geometry itself (windsor_i.png)
* force_mom_all.csv: contains force/moments for all runs in a single file
* force_mom_varref_all.csv: contains force/moments for all runs in a single file using a reference frontal area that is unique to each geometry
* geo_parameters_all.csv: contains all the geometry parameters for all the runs in a single file

<h3>Acknowledgements</h3>
-----------
* CFD solver and workflow development by Jordan Angel, Aditya Ghate, Gaetan Kenway, Man Long Wong, Cetin Kiris (Volcano Platforms) and Neil Ashton (Amazon Web Services, now NVIDIA)
* Geometry parameterization by Astrid Walle (Siemens Energy)
* Windsor advise and consultation by Gary Page (Loughborough University)
* Guidance on dataset preparation for ML by Danielle Maddix (Amazon Web Services)
* Simulation runs, HPC setup and dataset preparation by Neil Ashton (Amazon Web Services, now NVIDIA)

<h3>License</h3>
-----------
This dataset is provided under the CC BY SA 4.0 license, please see LICENSE.txt for full license text.
