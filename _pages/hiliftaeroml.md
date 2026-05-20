---
layout: page
permalink: /hiliftaeroml/
title: HiLiftAeroML
description: 
nav: false
nav_order: 2
---

<h3>Summary</h3>
---------
Machine Learning (ML) has the potential to revolutionise the field of aerospace engineering, enabling split-second aerodynamic predictions early in the design process.
However, the lack of open-source training data for complex aircraft configurations, using high-fidelity CFD methods, represents a major barrier to the development of AI surrogate models.
To address this, the first-ever open-source, high-fidelity public dataset of a high-lift aircraft has been generated for AI surrogate model development. The dataset is composed of 1,800 samples, arising from 180 geometry variants of the NASA Common Research Model (CRM-HL) evaluated across 10 angles of attack (from 4° to 22° in 2° increments). One of the key novelties of this dataset is the use of a GPU-accelerated high-fidelity explicit, wall-modeled LES (WMLES) approach on solution-adapted grids containing between 300 million and 500 million cells. By making this data publicly available under an open-source license, the aim is to accelerate the research and development of physical AI within the aerospace industry.

<img class="photo" alt="hiliftaeroml" src="{{ site.baseurl }}/assets/img/hiliftaero1.png">
<h3>CFD Solver:</h3>
----------
The simulations were performed using the "Fidelity Charles" flow-solver, an explicit, unstructured, finite-volume solver for the compressible Navier-Stokes equations. The simulations maintain a numerical accuracy of 2nd-order in space and 3rd-order in time.

<h3>How to download:</h3>
----------------

The dataset is openly accessible on Hugging Face without any additional costs. Below are some examples of how to download all or selected parts of the dataset. Please refer to the Hugging Face documentation for other ways of accessing the dataset and building pipelines.

<h5>Example 1: Download all files (~63TB compressed / 190TB unzipped)</h5>
--------
Please note you'll need to have git lfs installed first, then you can run the following command:

```
git clone git@hf.co:datasets/nvidia/hiliftaeroml
```

<h5>Example 2: Only download select files (STL, STP & forces and moments):</h5>
---------
Create the following bash script that can be adapted to loop through only select runs or to change to download different data files e.g. boundary/volume configurations.
```bash
#!/bin/bash

# Set the path and prefix
HF_OWNER="nvidia"
HF_PREFIX="hiliftaeroml"

# Set the local directory to download the files
LOCAL_DIR="./hiliftaero_data"

# Create the local directory if it doesn't exist
mkdir -p "$LOCAL_DIR"

# Loop through the geometry IDs (001 to 180) and Angles of Attack (4 to 22 in steps of 2)
for i in $(seq -f "%03g" 1 180); do
    for j in $(seq 4 2 22); do
        RUN_DIR="geo_LHC${i}_AoA_${j}"
        RUN_LOCAL_DIR="$LOCAL_DIR/$RUN_DIR"

        # Create the run directory if it doesn't exist
        mkdir -p "$RUN_LOCAL_DIR"

        # Download the geometry surface mesh (.stl)
        wget "[https://huggingface.co/datasets/$](https://huggingface.co/datasets/$){HF_OWNER}/${HF_PREFIX}/resolve/main/$RUN_DIR/geo_LHC${i}_AoA_${j}.stl" -O "$RUN_LOCAL_DIR/geo_LHC${i}_AoA_${j}.stl"

        # Download the surface geometry definition (.stp)
        wget "[https://huggingface.co/datasets/$](https://huggingface.co/datasets/$){HF_OWNER}/${HF_PREFIX}/resolve/main/$RUN_DIR/geo_LHC${i}_AoA_${j}.stp" -O "$RUN_LOCAL_DIR/geo_LHC${i}_AoA_${j}.stp"

        # Download the time-averaged aerodynamic coefficients (.csv)
        wget "[https://huggingface.co/datasets/$](https://huggingface.co/datasets/$){HF_OWNER}/${HF_PREFIX}/resolve/main/$RUN_DIR/force_mom_geo_LHC${i}_AoA_${j}.csv" -O "$RUN_LOCAL_DIR/force_mom_geo_LHC${i}_AoA_${j}.csv"
    done
done
```

<h3>Dataset Structure and Files:</h3>
-------
Each folder (e.g., `geo_LHCi_AoA_j` where `i` is the geometry ID from 001 to 180 and `j` is the angle of attack) corresponds to a specific geometric variant and flow condition. Inside each run folder, you will find:

* `boundary_geo_LHCi_AoA_j.vtu.tgz`: Time-averaged flow quantities mapped onto the surface boundary (~13 GB compressed, 21 GB unzipped).
* `volume_geo_LHCi_AoA_j.vtu.tgz`: Time-averaged flow quantities within the domain volume field (~23 GB compressed, 86 GB unzipped).
* `geo_LHCi_AoA_j.stl`: Surface mesh (triangles) representation of the geometry (~197 MB).
* `geo_LHCi_AoA_j.stp`: CAD surface geometry definition file (~48 MB).
* `force_mom_geo_LHCi_AoA_j.csv`: Time-averaged drag, lift, moment, and integrated pressure/viscous coefficients.
* `geo_values_geo_LHCi_AoA_j.csv`: Reference geometric parameter values used to define the vehicle shape via the DoE (Design of Experiments) method.
* `ref_values_geo_LHCi_AoA_j.csv`: General flow reference metrics such as reference area, dynamic pressure (Q), and AoA.
* `img_wss_LHCi_AoA_j.png`: High-resolution visual rendering of the wall shear stress and skin-friction distribution on the aircraft surface.
* `plot_CD_geo_LHCi_AoA_j.png`, `plot_CL_geo_LHCi_AoA_j.png`, `plot_CM_geo_LHCi_AoA_j.png`: Time-series convergence plots tracking the evolution of the Drag, Lift, and Pitching Moment Coefficients.

In addition to the per-run directories, the root repository path contains unified tracking data:
* `geo_values_all.csv`: Compiled master reference geometry definitions across all executed runs.
* `force_mom_all.csv`: Consolidated master time-averaged drag, lift, moment, and force component coefficients for the entire dataset matrix.
* `splits/`: A folder containing the baseline data train/val/test splits (`manifest.json`) alongside an accompanying explanatory design breakdown document (`README.pdf`).

<h3>Credits and Acknowledgements</h3>
-----
The dataset was built and released through an industry-leading collaborative initiative between **NVIDIA**, **Cadence Design Systems**, and **The Boeing Company**.

<h3>License</h3>
----
This dataset is published and provided under the permissive, open-source **Creative Commons Attribution 4.0 International (CC BY 4.0)** license. Users are free to share, copy, and adapt the material for any purpose, including commercial workflows, provided proper credit is given to the original creating authors.
