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

The dataset is now available on HuggingFace. Below are some examples of how to download all or selected parts of the dataset. Please refer to the HuggingFace documentation for other ways to accessing the dataset and building workflows.

<h5>Example 1: Download all files (~2TB)</h5>
--------
Please note you'll need to have git lfs installed first, then you can run the following command:

```
git clone git@hf.co:datasets/neashton/ahmedml
```

<h5>Example 2: only download select files (STL,images & force and moments):</h5>
---------
Create the following bash script that could be adapted to loop through only select runs or to change to download different files e.g boundary/volume.
```
#!/bin/bash

# Set the S3 bucket and prefix
HF_OWNER="neashton"
HF_PREFIX="ahmedml"

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
    wget "https://huggingface.co/datasets/${HF_OWNER}/${HF_PREFIX}/resolve/main/$RUN_DIR/ahmed_$i.stl" -O "$RUN_LOCAL_DIR/ahmed_$i.stl" 

    # Download the force_mom_i.csv file
    wget "https://huggingface.co/datasets/${HF_OWNER}/${HF_PREFIX}/resolve/main/$RUN_DIR/force_mom_$i.csv" -O "$RUN_LOCAL_DIR/force_mom_$i.csv" 

done
```

<h3>Files:</h3>
-------
Each folder (e.g run_1,run_2...run_"i" etc) corresponds to a different geometry that contains the following files where "i" is the run number:
* ahmed_i.stl : geometry stl (~5mb):
* geo_parameters_1.csv (missing run 500): parameters that define the geometry
* boundary_i.vtp : Boundary VTP (~500mb)
* volume_i.vtu : Volume field VTU (~5GB)
* force_mom_i.csv : forces (Cd,Cl) time-averaged with constant reference area
* force_mom_varref_i.csv : forces (Cd,Cl) time-averaged with varying reference area
* slices : folder containing .vtp slices in x,y,z that contain flow-field variables
* images : (folder) that contains images of the following variables (CpT, UxMean) for slices of the domain in the X,Y & Z locations.

In addition we provide:
* force_mom_all.csv : run, cd,cl for all runs in a single file
* force_mom_varref_all.csv : run, cd,cl for all runs in a single file with varying reference area
* geo_parameters_all.csv : all the geometry parameters for each run inside a single file
* ahmedml.slvs : SolveSpace input file to create the parametric geometries
* stl : folder containing stl files that were used as inputs to the OpenFOAM process
* openfoam-casesetup.tgz : complete OpenFOAM setup that can be used to extend or reproduce the dataset

<h3>Acknowledgements </h3>
---------
* OpenFOAM solver and workflow development by Neil Ashton (Amazon Web Services - now NVIDIA)
* Geometry parameterization by Samuel Gundry (Amazon Web Services) and Parisa Shabestari (Amazon Web Services)
* Guidance on dataset preparation for ML by Danielle Madix (Amazon Web Services)
* Simulation runs, HPC setup and dataset preparation by Neil Ashton (Amazon Web Services - now NVIDIA)

<h3> License </h3>
--------
This dataset is provided under the CC BY SA 4.0 license, please see LICENSE.txt within the dataset for full license text
