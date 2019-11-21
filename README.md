# hcg_hi_pipeline
A CASA and Python based pipeline for reducing VLA HI spectral line data of HCGs.

## Prerequisites
This pipeline was developed using [CASA](https://casa.nrao.edu/casa_obtaining.shtml) v5.4.2-5. It also requires the [Analysis Utilities](https://casaguides.nrao.edu/index.php/Analysis_Utilities) library.

## Getting started

In order to run the pipeline you will first need to modify 2 files: PROJECTID_params.cfg and hi_segmented_pipeline.yml. The required changes are as follows:
  1. Replace every instance of "PROJECTID" in both files (including the parameters file name) with an name or code for your project.
  2. In the parameters file specify the path to the raw VLA data you wish to process.
  3. In the pipeline yaml file specify the new name of the parameters file under the variable "configfile".
  4. In the pipeline yaml file specify the path to your installation of CASA.

Each of these points in the files are highlighted with a "CHANGME" comment next to them.
