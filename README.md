# HI pipeline for historical VLA data (of HCGs)
A CASA and Python based pipeline for reducing VLA HI spectral line data. The pipeline was created primarily for processing historical VLA observations of Hickson Compact Groups.

## Prerequisites
This pipeline was developed using [CASA](https://casa.nrao.edu/casa_obtaining.shtml) v5.4.2-5. It also requires the [Analysis Utilities](https://casaguides.nrao.edu/index.php/Analysis_Utilities) library. All of the Python dependencies are listed in "conda_env.yml" which defines a [Conda](https://docs.conda.io/en/latest/) environment that can be constructed as described [here](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-from-an-environment-yml-file).

## Getting started

In order to run the pipeline you will first need to copy 2 files ("PROJECTID_params.cfg" and "hi_segmented_pipeline.yml") to your execution directory and then modify them as follows:
  1. Replace every instance of "PROJECTID" in both files (including the parameters file name) with a name or code for your project. This will be used as the base name for the measurement set (e.g. "PROJECTID.ms").
  2. In the parameters file specify the path to the raw VLA data you wish to process. If using historical VLA data then this should be the path to the directory containing any ".xp" files you want to import. These should be the only files in that directory as the pipeline will blindly try to import everything it finds. It will import these files and construct a measurement set in the local directory. For JVLA data this should be the path to the directory above the "PROJECTID.ms" directory. In this case the pipeline will create a symbolic link to avoid copying the data. Therefore, it is vital that the value of "PROJECTID" you set in step 1 matches the existing measurement set name.
  3. In the pipeline yaml file specify the new name of the parameters file under the variable "configfile". Normally this will be "PROJECTID_params.cfg".
  4. In the pipeline yaml file specify the path to the directory containing the CASA executable.
  5. In the pipeline yaml file define the scripts value as the path to the directory containing the pipeline scipts (e.g. ~/hcg_hi_pipeline/).

Each of these points in the files are highlighted with a "CHANGEME" comment next to them. You will also need to (manually) make a symbolic link to the the 'hi_segmented_pipeline.py' script in your execution directory. If the files 'hi_segmented_pipeline.py', 'hi_segmented_pipeline.yml', and 'PROJECTID_params.cfg' are all present in the execution directory, then the pipeline will construct the remaining necessary links and copy the raw data (if a historical VLA data set, data from JVLA observations is not duplicated, merely linked to).

## Running the pipeline

The pipeline has 7 steps which are chained together using the [CGAT-core](https://github.com/cgat-developers/cgat-core) workflow management system such that each step is aware that it depends on previous steps. The pipeline also registers any changes to the "PROJECTID_params.cfg" parameters file since the previous execution of the pipeline. Any necessary steps will be automatically repeated when parameters are altered.

The 7 steps are:
  1. 'import_data': Converts the raw data into CASA measurement set format (unless already the case). May also transform the measurement set. In interactive mode the user will be queried to decide this.
  2. 'flag_calib_split': This step flags, calibrates and splits off the individual targets from the full data set. Flagging is done through the automated algorithms available in CASA. However, the user may create a manual list of flags in a file named 'manual_flags.list' in the execution directory and the pipeline will include these as well (such flags must be in CASA's [list format](https://casa.nrao.edu/casadocs/casa-5.4.1/global-task-list/task_flagdata/about)). If the pipeline is run in interactive mode the user is queried to specify which sources are calibrators and targets in order for the data to be correctly calibrated. Further automatic flagging is performed on the (first round) calibrated data and then the calibration is re-run a second time. Finally the target objects are split off into separate measurement sets.
  3. 'dirty_cont_image': A dirty image (without the continuum emission removed) is produced for each target.
  4. 'contsub_dirty_image': The user is queried to specify the emission line-free channels for each target. The continuum is then removed from the uv data. Another dirty image of each target is produced, but now with the continuum removed.
  5. 'clean_image': The expected noise level based on the integration time and the amount of flagging is estimated and a clean image is generated using the CASA task tclean. Generates fits cubes for each target with and without a primary beam correction.
  6. 'moment_zero': This creates a simple moment zero map of the emission, including all pixels above a given S/N threshold (set in the parameters file). 
  7. 'cleanup': This step deleted various files created by the workflow to save space. However, note that running this step effectively finalises the products of the pipeline and it may be necessary to begin again from step 1 if any changes need to be made. There are 3 cumulative levels of this function (set in the PROJECTID_params.cfg file): 1) deletes files connected to the uncalibrated data (steps before splitting must be repeated), 2) deletes excess files produce when generating images (all imaging must be repeated), 3) deletes all files produced in imaging except the final fits cubes (cubes in CASA format and the residuals cubes are lost).
  
To execute a particular step of the pipeline use a command equivalent to the following:

```bash
python hi_segmented_pipeline.py make moment_zero --local
```

The workflow will know what previous steps are required for any individual step and will run them as needed. It will also recognise if previous steps have been re-run and the changes need to be propagated along the workflow before running the requested step. In addition, if you manually modify parameters within the "PROJECTID_params.cfg" file, the workflow will automatically recognise which previous steps (if any) need to be repeated before running the requested step. If for some reason you need to repeat a step without modifying the parameters, this can be achieved by manually deleting its associated ".done" file before executing the step in the workflow.

The pipeline is intended to be run in interactive mode on its first execution. In the mode it will halt at several points and ask the user for input so that the data can be processed as they wish. However, this feature can be disabled by setting the 'interactive' parameter to 'False' in the parameters file. The entire pipeline can be run at once by setting all the necessary parameters in the parameters file, but in interactive mode many potentially illegal parameter values can be corrected on the fly, whereas in non-interactive mode these will generally cause the pipeline to fail. If you wish to run the pipeline in non-interactive mode then please see the parameters guide below.


## Parameter descriptions

global:
- project_name: This will be used as the base name for the measurement set. If you are using JVLA data that was already downloaded in ms format, it is important that this name matches that of the existing ms (minus the ".ms" extention).
- rest_freq: This should be "1420405751.786Hz" unless not working with HI, which is not advised.
- interactive: True/False. If true the pipeline will halt at various points to query the user. If false it will attempt to run without user input. Note that running in interactive mode can help to catch errors in the parameter values that might cause the pipeline to crash, however, it means it cannot be left to run unattended.
- src_dir: Name of directory to store split source files in.
- img_dir: Name of directory to store images in.
- mom_dir: Name of directory to store moments in.
- cleanup_level: Integer from 0-3. Sets the level of tidying done (see above).
- (ignore_errs: True/False. "Hidden" parameter that deactivates the function that checks the casalog for severe errors after each task. It is inadvisable to use this except in exceptional circumstances or for the purposes of debugging.)

importdata:
- data_path: The path from the execution directory (or the absolute path) to the directory where the raw data are saved. If working with JVLA data this should be the path to the directory above the ms directory, not the ms directory itself.
- jvla: True/False. Are you using histoorical or JVLA data? This determines whether the data are copied to the execution directory (historical data are assumed to be relatively small) or is a symbolic link is made to an existing ms (as well a several other minor differences in the flagging and calibration steps).
- mstransform: True/False. Do you want to transform the measurement set when you import it?
- keep_obs: (String in single quotes.) List of the observation blocks to keep when running mstransform e.g. '0,1,4'.
- keep_spws: (String in single quotes.) List of the spectral windows to keep when running mstransform e.g. '0,1,4'.
- keep_fields: (String in single quotes.) List of the fields to keep when running mstransform e.g. '0,1,4' or '3C48, HCG22'.
- hanning: True/False. Apply Hanning smoothing to the data when importing it?
- chanavg: Number of channels to average together when importing the data (0 for no averaging). Note if the "hanning" parameter is set to True, then this smoothing will be performed in addition to Hanning smoothing, not instead of it.

flagging:
- shadow_tol: Float. The number of metres of dish overlap that is tolerated before the data are flagged for the shadowed antenna.
- quack_int: Float. The number of seconds removed from the beginning of each scan to allow time for dishes to settle.
- timecutoff: Float.

... Work in progress.
