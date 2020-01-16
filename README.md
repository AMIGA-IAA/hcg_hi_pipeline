# hcg_hi_pipeline
A CASA and Python based pipeline for reducing VLA HI spectral line data of HCGs.

## Prerequisites
This pipeline was developed using [CASA](https://casa.nrao.edu/casa_obtaining.shtml) v5.4.2-5. It also requires the [Analysis Utilities](https://casaguides.nrao.edu/index.php/Analysis_Utilities) library. We are in the process of developing a conda environment to handle the necessary Python packages.

## Getting started

In order to run the pipeline you will first need to modify 2 files: PROJECTID_params.cfg and hi_segmented_pipeline.yml. The required changes are as follows:
  1. Replace every instance of "PROJECTID" in both files (including the parameters file name) with an name or code for your project.
  2. In the parameters file specify the path to the raw VLA data you wish to process.
  3. In the pipeline yaml file specify the new name of the parameters file under the variable "configfile".
  4. In the pipeline yaml file specify the path to your installation of CASA.

Each of these points in the files are highlighted with a "CHANGME" comment next to them.

## Running the pipeline

The pipeline has 6 steps which are chained together using the [CGAT-core](https://github.com/cgat-developers/cgat-core) workflow management system such that each step is aware that it depends on previous steps.

The 6 steps are:
  1. 'import_data': Converts the raw data into CASA measurement set format (unless already the case).
  2. 'flag_calib_split': This step flags, calibrates and splits off the individual targets from the full data set. Flagging is done through the automated algorithms available in CASA. However, the user may create a manual list of flags in a file named 'manual_flags.list' in the execution directory and the pipeline will include these as well (such flags must be in CASA's [list format](https://casa.nrao.edu/casadocs/casa-5.4.1/global-task-list/task_flagdata/about)). If the pipeline is run in interactive mode the user is the queries to specify which sources are calibrators and targets in order for the data to be correctly calibrated. Further automatic flagging is performed on the (first round) calibrated data and then the calibration is re-run a second time. Finally the target objects are split off into separate measurement sets.
  3. 'dirty_cont_image': A dirty image (without the continuum emission removed) is produced for each target.
  4. 'contsub_dirty_image': The user is queried to specify the emission line-free channels for each target. The continuum is then removed from the uv data. Another dirty image of each target is produced, but now with the continuum removed.
  5. 'clean_image': The expected noise level based on the integration time and the amount of flagging is estimated and a clean image is generated using the CASA task tclean. Generates fits cubes for each target with and without a primary beam correction.
  6. 'cleanup': This step deleted various files created by the workflow to save space. However, note that running this step effectively finalises the products of the pipeline and it may be necessary to begin again from step 1 if any changes need to be made. There are 3 cumulative levels of this function (set in the PROJECTID_params.cfg file): 1) deletes files connected to the uncalibrated data (steps before splitting must be repeated), 2) deletes excess files produce when generating images (all imaging must be repeated), 3) deletes all files produced in imaging except the final fits cubes (cubes in CASA format and the residuals cubes are lost).
  
To execute a particular step of the pipeline use a command equivalent to the following:

```bash
python hi_segmented_pipeline.py make clean_image --local
```

The workflow will know what previous steps are required for any individual step and will run them as needed. It will also recognise if previous steps have been re-run and the changes need to be propagated along the workflow before running the requested step. In addition, if you manually modify parameters within the PROJECTID_params.cfg file, the workflow will automatically recognise which previous steps (if any) need to be repeated before running the requested step. If for some reason you need to repeat a step without modifying the parameters, this can be achieved by manually deleting its associated .done file before executing the step in the workflow.

The pipeline is intended to be run in interactive mode on its first execution. In the mode it will halt at several points and ask the user for input so that the data can be process as they wish. However, this feature can be disabled by setting the 'interactive' parameter to 'False' in the PROJECTID_params.cfg file. The entire pipeline can be run at once by setting all the necessary parameters in the parameters file, but in interactive mode many potentially illegal parameter values can be corrected on the fly, whereas in non-interactive mode these will generally cause the pipeline to fail.
