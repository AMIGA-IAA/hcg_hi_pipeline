# Step by step example of implementing the pipeline for HCG 16

1. If you do not already have all the prerequistes listed in the documentation then: Install [git](https://git-scm.com/). Install [CASA](https://casa.nrao.edu/casa_obtaining.shtml), we recommend [CASA 5.4](https://casa.nrao.edu/download/distro/casa/release/el7/casa-release-5.4.2-5.el7.tar.gz) for maximum compatiblity, but the pipeline should also function with any CASA 5 version. Install CASA [Analysis Utilities](https://casaguides.nrao.edu/index.php/Analysis_Utilities). Install [Ananconda](https://www.anaconda.com/) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

2. Clone the github repo to you local machine with the terminal command:

```
git clone https://github.com/AMIGA-IAA/hcg_hi_pipeline.git
```

3. Construct the conda environment: `conda env create -f environment.yml`. Activate it: `conda activate hcg_hi_pipeline`.

4. Move into this example directory and download and unpack the raw VLA data with the following commands:
    - `cd pipeline_example`
    - `wget "https://b2share.eudat.eu/api/files/831f14fa-1840-454c-819b-d0b61500583b/hcg16-data.tar.gz"`
    - `tar -xzf hcg16-data.tar.gz AW234_B891206.xp1 AW500_C990113.xp1 AW500_D990114.xp1`
    - `mkdir AW234/raw_data`
    - `mkdir AW500/raw_data`
    - `mv AW234*.xp1 AW234/raw_data/.`
    - `mv AW500*.xp1 AW500/raw_data/.`
    
5. Move into the AW234 directory and create a symbolic link to the main pipeline script and copy the pipeline parameters file:
    - `cd AW234`
    - `ln -s ../../hi_segmented_pipeline.py`
    - `cp ../../hi_segmented_pipeline.yml .`

6. In the 'hi\_segmented\_pipeline.yml' you will need to set the absolute paths to CASA (e.g. /home/user/software/CASA/casa-release-5.4.2-8.el7/bin/), the top directory of this repo (e.g. /home/user/software/hcg\_hi\_pipeline/), the name of the pipeline parameters file for this dataset (AW234\_params.cfg), and a project name (AW234).

7. Check your execution environment by running the first step `import_data`. The AW234\_params.cfg is an edited version of the template parameters file in the top repo directory PROJECTID\_params.cfg. See the parameters description in the main README file for an explanation of all of the parameters. To ensure everything is setup correctly begin by running (remember the conda environment must be active) just the first step of the pipeline: `python hi_segmented_pipeline.py make import_data --local`. If the paths in hi\_segmented\_pipeline.yml are correctly set this step will create symbolic links to all the other pipeline scripts and load the raw data into the CASA MS format. A common error at this stage is for CASA to complain that the leap second tables are out of date. For historical VLA data this isn't a problem, but it's good practice to [keep it up to date](https://casaguides.nrao.edu/index.php/Fixing_out_of_date_TAI_UTC_tables_(missing_information_on_leap_seconds)), and the pipeline will not allow you to continue while a severe error is present. To check for errors either scroll through the terminal output or open AW234.log. Ensure this step executes correctly before continuing. You should see a message containing `INFO Completed Task = 'import_data'` followed by the execution time. Note that this step will momentarily produce a plotting window, therefore if you are running this on a machine with only terminal access and no X-forwarding this may result in a crash.

8. After successfully importing the data you can attempt to execute the entire pipeline: `python hi_segmented_pipeline.py make moment_zero --local`. Note that the import data step will not be repeated. However, if you had gone to the parameters file and modified one of the parameters listed under 'importdata' then the pipeline would automatically know to repeat this step before executing the remainder of the pipeline (this applies to all steps in the pipeline).

9. After the pipeline has finished you can view the resulting images in CASA viewer (e.g `casaviewer moments/HCG16.mom0.fits`) or another FITS viewer of your choice. You can also experiment with modifying parameters in the parameters file and instructing the pipeline to re-run the make moment zero step.

10. Move to the AW500 directory. Copy over the hi\_segmented\_pipeline.yml file and replace the 'AW234' values with 'AW500'. Create another symbolic link to the master script: `ln -s ../../hi_segmented_pipeline.py`.

11. Repeat steps 7-9 for AW500.

12. Return to the main example directory and them move to the combined\_imaging directory. Make symbolic links to both combined imaging scripts in the master repo.
    - `ln -s ../../combined_imaging/combine_dirty_image.py`
    - `ln -s ../../combined_imaging/combine_clean_image.py`
    - `ln -s ../../common_functions.py`
    
13. The parameters file here is a modified version of the master template. To create the combined dirty image run the command: `casa -c combine_dirty_image.py HCG16_params.cfg`. This step is technically unnecessary in this case, but it is often useful to first create a dirty image, before proceeding to a clean image, in order to check that the parameters are set appropriately. Finally to create the clean image run: `casa -c combine_clean_image.py HCG16_params.cfg`.
