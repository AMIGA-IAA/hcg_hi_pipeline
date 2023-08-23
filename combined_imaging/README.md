# CASA scripts for combining and imaging multiple uv datasets

The scripts combine_dirty_image.py and combine_clean_image.py will combine multiple uv datasets (already continuum subtracted) listed in a parameters file and produce dirty and clean images respectively.

## Executing the scripts

Both scripts are designed to run within CASA and are executed as follows:

```bash
casa -c combine_dirty_image.py HCG57_params.cfg
```

The dirty image script is designed to allow you to test the parameters before proceeding to the longer clean imaging step. However, even if you have decided all parameters a priori you still need to exeute the dirty image script before the clean image script, as the latter script expects outputs from the former.

## Parameters

combine:
- HCG: Taregt ID number (in this case for HCG).
- proj_IDs: List of strings which are the project IDs. The script assumes that the uv data for each project can be found ```../PROJECTID/sources/HCGID*.*split.contsub```. Sorry, for the moment the 'HCG' is hard coded in the script.

image:
- rms: Estimate of the rms noise in mJy. The clean image script will clean down to 2.5 x rms.
- phasecenter: If the pointing/phase centre of all the datasets are the same then this parameter can be left as a blank string. However, if not then it is strongly advised that you specify a new phasecenter as a string e.g. 'J2000 03:03:30 -15.35.32.5'.
- im_size: Number of pixels on a side (images are square).
- pix_size: The angular size of a pixel e.g. '4arcsec'.
- scales: List of integers/floats indicating the scales (in pixels) that will be used by the multi-scale clean algorithm. The default values assume the pixel size will be set so that there are 5 pixels across the synthesised beam. Be careful that the largest scale is still constrained by the uv data or imaging may diverge (see [here](https://science.nrao.edu/facilities/vla/docs/manuals/oss/performance/resolution)).
- im_chans: A string (that can be blank, i.e. select all) indicating the spectral window and channels to image e.g. '0:11~21'.
- gridder: The gridder that CASA will use to produce the final image. Examples are 'wproject', 'mosaic', and 'standard'. 
- rest_freq: You probably don't want to change this from '1420405751.786Hz', why would you look at any other line? Seriously though, this whole pipeline was designed specifically with HI in mind and is entirely untested on any other line.
- robust: Brigg's robust parameters. The default value of 2 is designed to maximise sensitivity to extended features at the expense of resolution.
- automask_sl: CASA automasking side lobe threshold (see [here](https://casaguides.nrao.edu/index.php/Automasking_Guide)).
- automask_ns: CASA automasking noise threshold (see [here](https://casaguides.nrao.edu/index.php/Automasking_Guide)).
- automask_mbf: CASA automasking minimum beam fraction parameter (see [here](https://casaguides.nrao.edu/index.php/Automasking_Guide)).
- automask_lns: CASA automasking low noise threshold (see [here](https://casaguides.nrao.edu/index.php/Automasking_Guide)).
- automask_neg: CASA automasking negative threshold (see [here](https://casaguides.nrao.edu/index.php/Automasking_Guide)).
