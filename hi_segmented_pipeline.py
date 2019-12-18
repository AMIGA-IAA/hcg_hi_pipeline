#!/usr/bin/env python

import sys
import os
import logging
import time
import numpy
import shutil
import readline
import logging
import configparser
from ast import literal_eval
import glob
import collections

from ruffus import *
import cgatcore.experiment as E
from cgatcore import pipeline as P


def input_validation():
    """
    Auxiliary function to make sure input configuration is valid
    """

    # check whether 'configfile' was specified in pipeline.yml
    if 'configfile' not in cgatcore_params:
        raise RuntimeError(' Please specify a configfile in pipeline.yml ')

    # check whether configfile is readable
    if not os.access(cgatcore_params['configfile'], os.R_OK):
        raise FileNotFoundError(' Configuration file is required but not found.')
        
    # check casa path exists
    if not os.access(cgatcore_params['casa'] + '/casa', os.R_OK):
        raise FileNotFoundError(' CASA is required but not found. Check path in yml file.')
        
    # check project ID exists
    if cgatcore_params['project'] == '':
        raise ValueError(' Project ID is required but not found.')
        
    
        



# Read cgat-core configuration
cgatcore_params = P.get_parameters("hi_segmented_pipeline.yml")

# Sanity checks on input parameters
input_validation()

# Add CASA to the PATH
os.environ["PATH"] += os.pathsep + cgatcore_params['casa']

# deactivate cgat-core logging to stdout
# cgat-core logs were sent to both stdout and pipeline.log
# to-do: we want to have it enable only for pipeline.log
logging.getLogger("cgatcore.pipeline").disabled = False
logging.getLogger("cgatcore").disabled = False




# start of the cgat-core pipeline
@originate('dependency_check.done')
def dependency_check(outfile):
    """
    Check required dependencies to run the pipeline
    """
    deps = ["casa"]
    for cmd in deps:
        if shutil.which(cmd) is None:
            raise EnvironmentError("Required dependency \"{}\" not found".format(cmd))
    
    scripts = ['import_data','flag_calib_split','dirty_cont_image','contsub_dirty_image','clean_image','cleanup','common_functions']
    for script in scripts:
        if not os.access(script+'.py', os.R_OK):
            os.symlink(cgatcore_params['scripts']+script+'.py',script+'.py')
        if not os.access(script+'.py', os.R_OK):
            os.unlink(script+'.py')
            raise FileNotFoundError('{0}.py file is required but not found in the scripts directory ({1}).'.format(script,cgatcore_params['scripts']))

    open(outfile, 'a').close()
    
    

@transform(dependency_check, suffix('dependency_check.done'), 'import_data.done'.format(cgatcore_params['project']))
def import_data(infile,outfile):
    statement = 'casa -c import_data.py {} && touch import_data.done'.format(cgatcore_params['configfile'])
    stdout, stderr = P.execute(statement)
    #print('stdout: {}'.format(stdout.decode("utf-8")))
    #print('stderr: {}'.format(stderr.decode("utf-8")))
    
@transform(import_data, suffix('import_data.done'.format(cgatcore_params['project'])), 'flag_calib_split.done'.format(cgatcore_params['project']))
def flag_calib_split(infile,outfile):
    statement = 'casa -c flag_calib_split.py {} && touch flag_calib_split.done'.format(cgatcore_params['configfile'])
    stdout, stderr = P.execute(statement)
    #print('stdout: {}'.format(stdout.decode("utf-8")))
    #print('stderr: {}'.format(stderr.decode("utf-8")))
    
@transform(flag_calib_split, suffix('flag_calib_split.done'.format(cgatcore_params['project'])), 'dirty_cont_image.done'.format(cgatcore_params['project']))
def dirty_cont_image(infile,outfile):
    statement = 'casa -c dirty_cont_image.py {} && touch dirty_cont_image.done'.format(cgatcore_params['configfile'])
    stdout, stderr = P.execute(statement)
    #print('stdout: {}'.format(stdout.decode("utf-8")))
    #print('stderr: {}'.format(stderr.decode("utf-8")))
    
@transform(dirty_cont_image, suffix('dirty_cont_image.done'.format(cgatcore_params['project'])), 'contsub_dirty_image.done'.format(cgatcore_params['project']))
def contsub_dirty_image(infile,outfile):
    statement = 'casa -c contsub_dirty_image.py {} && touch contsub_dirty_image.done'.format(cgatcore_params['configfile'])
    stdout, stderr = P.execute(statement)
    #print('stdout: {}'.format(stdout.decode("utf-8")))
    #print('stderr: {}'.format(stderr.decode("utf-8")))
    
@transform(contsub_dirty_image, suffix('contsub_dirty_image.done'.format(cgatcore_params['project'])), 'clean_image.done'.format(cgatcore_params['project']))
def clean_image(infile,outfile):
    statement = 'casa -c clean_image.py {} && touch clean_image.done'.format(cgatcore_params['configfile'])
    stdout, stderr = P.execute(statement)
    #print('stdout: {}'.format(stdout.decode("utf-8")))
    #print('stderr: {}'.format(stderr.decode("utf-8")))
    
@transform(clean_image, suffix('clean_image.done'.format(cgatcore_params['project'])), 'cleanup.done'.format(cgatcore_params['project']))
def cleanup(infile,outfile):
    statement = 'casa -c cleanup.py {} && touch cleanup.done'.format(cgatcore_params['configfile'])
    stdout, stderr = P.execute(statement)
    #print('stdout: {}'.format(stdout.decode("utf-8")))
    #print('stderr: {}'.format(stderr.decode("utf-8")))
    

def main(argv=None):
    if argv is None:
        argv = sys.argv
    P.main(argv)

if __name__ == "__main__":
    sys.exit(P.main(sys.argv))