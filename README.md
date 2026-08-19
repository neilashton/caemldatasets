# CAE ML Datasets

This repository contains the source for [caemldatasets.org](https://caemldatasets.org/), a catalogue and documentation hub for open, high-fidelity computational-fluid-dynamics datasets used in scientific machine-learning research.

## Dataset catalogue

| Dataset | Domain | Cases | Paper | Data | Licence |
| --- | --- | ---: | --- | --- | --- |
| AhmedML | Automotive aerodynamics | 500 geometries | [arXiv:2407.20801](https://arxiv.org/abs/2407.20801) | [Hugging Face](https://huggingface.co/datasets/neashton/ahmedml) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| WindsorML | Automotive aerodynamics | 355 geometries | [arXiv:2407.19320](https://arxiv.org/abs/2407.19320) | [Hugging Face](https://huggingface.co/datasets/neashton/windsorml) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| DrivAerML | Automotive aerodynamics | 500-geometry design space; 484 public cases | [arXiv:2408.11969](https://arxiv.org/abs/2408.11969) | [Hugging Face](https://huggingface.co/datasets/neashton/drivaerml) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| HiLiftAeroML | Aerospace aerodynamics | 1,800 cases | [arXiv:2605.19565](https://arxiv.org/abs/2605.19565) | [Hugging Face](https://huggingface.co/datasets/nvidia/HiLiftAeroML) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

The datasets themselves are not stored in this Git repository. Download data from the linked Hugging Face repositories after reviewing each dataset card, licence, documented limitations and storage requirements. The website also publishes technical comparison material, official benchmark-split packages and selective-download guidance.

## Local development

The website uses Jekyll and the Ruby dependencies recorded in `Gemfile.lock`. Ruby 3.2.2 matches the deployment workflow.

```bash
bundle install
bundle exec jekyll serve
```

Open <http://localhost:4000> to view the local site. A production build can be checked with:

```bash
JEKYLL_ENV=production bundle exec jekyll build
```

## Contributions and contact

Corrections to the catalogue and documentation improvements are welcome through an issue or pull request. Dataset questions, corrections and examples of published work using these resources can be sent to [contact@caemldatasets.org](mailto:contact@caemldatasets.org).

## Theme and licences

The site is based on the [al-folio](https://github.com/alshedivat/al-folio) Jekyll theme. Website source code is available under the repository's [MIT License](LICENSE). Dataset content is governed separately by the licence shown in the table and on its Hugging Face dataset card.
