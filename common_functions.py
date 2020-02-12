import time
import os
import sys
import filecmp
import numpy
import shutil
import readline
import logging
import ConfigParser
from ast import literal_eval
import glob
import collections


# Read configuration file
def read_config(configfile):
    '''
    Parses the configuration file of parameters passed when the pipeline is executed.
    
    Input:
    configfile = Path to configuration file. (String)
    
    Output:
    config = The parameters read from the file. (Ordered dictionary)
    config_raw = The instance of the parser.
    '''
    if not os.path.isfile(configfile):
        print('configfile: {} not found'.format(configfile))
        sys.exit(-1)
    config_raw = ConfigParser.RawConfigParser()
    config_raw.read(configfile)
    config = config_raw._sections
    for key in config.keys():
        config[key].pop('__name__')
        for key2 in config[key].keys():
            try:
                config[key][key2] = literal_eval(config[key][key2])
            except ValueError:
                pass
            except SyntaxError:
                pass
    return config,config_raw

# Utilities
def makedir(pathdir,logger):
    '''
    Makes new directory.
    
    Input:
    pathdir = Path for new directory to create. (String)
    '''
    try:
        os.mkdir(pathdir)
        logger.info('Create directory: {}'.format(pathdir))
    except:
        logger.debug('Cannot create directory: {}'.format(pathdir))
        pass

def rmdir(pathdir,logger):
    '''
    Removes an entire directory.
    
    Input:
    pathdir = Path of the directory to be removed. (String)
    '''
    if os.path.exists(pathdir):
        try:
            shutil.rmtree(pathdir)
            logger.info('Deleted: {0}'.format(pathdir))
        except:
            logger.debug('Could not delete: {0}'.format(pathdir))
            pass
        
def mvdir(pathdir, newdir, logger):
    '''
    Moves an entire directory.
    
    Input:
    pathdir = Path of the directory to be moved. (String)
    '''
    if os.path.exists(pathdir):
        try:
            shutil.move(pathdir,newdir)
            logger.info('Moved {0} to {1}'.format(pathdir,newdir))
        except:
            logger.debug('Could not move: {0}'.format(pathdir))
            pass


def rmfile(pathdir,logger):
    '''
    Removes an file.
    
    Input:
    pathdir = Path of the file to be removed. (String)
    '''
    if os.path.exists(pathdir):
        try:
            os.remove(pathdir)
            logger.info('Deleted: {0}'.format(pathdir))
        except:
            logger.debug('Could not delete: {0}'.format(pathdir))
            pass
        
#User input function
def uinput(prompt, default=''):
    '''
    Prompts the user to input a string and provides a default.
    
    Input:
    prompt = Input prompt. (String)
    default = Default input. (String)
    
    Output:
    Final string entered by user. (String)
    '''
    readline.set_startup_hook(lambda: readline.insert_text(default))
    try:
        return raw_input(prompt)
    finally:
        readline.set_startup_hook()


# Set up the logger
def get_logger(    
        LOG_FORMAT     = '%(asctime)s | %(levelname)s | %(message)s',
        DATE_FORMAT    = '%Y-%m-%d %H:%M:%S',
        LOG_NAME       = 'logger',
        LOG_FILE_INFO  = 'mylog.log',
        LOG_FILE_ERROR = 'errors.log',
        new_log = False):

    """ Set up a logger with UTC timestamps"""
    logger = logging.getLogger(LOG_NAME)
    log_formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
    logging.Formatter.converter = time.gmtime

    ## comment this to suppress console output    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler) 

    # File mylog.log with all information
    if new_log:
        mode = 'w'
    else:
        mode = 'a+'
    file_handler_info = logging.FileHandler(LOG_FILE_INFO, mode=mode)
    file_handler_info.setFormatter(log_formatter)
    file_handler_info.setLevel(logging.INFO)
    logger.addHandler(file_handler_info)
    
    logger.setLevel(logging.INFO)
    return logger

def diff_pipeline_params(configfile,logger):
    """
    Prints a diff of the final and backed up versions of the pipeline parameters.
    """
    backup_file = 'backup.'+configfile
    if not filecmp.cmp(backup_file,configfile):
        logger.info('The parameters in {} have been modified during this pipeline step.'.format(configfile))
        bash_command = 'diff {0} {1} > diff_params.txt'.format(backup_file,configfile)
        os.system(bash_command)
        f = open('diff_params.txt','r')
        diff_lines = f.readlines()
        f.close()
        rmfile('diff_params.txt',logger)
        logger.info('The changes are as follows:')
        for line in diff_lines:
            logger.info(line)
            
def backup_pipeline_params(configfile,logger):
    """
    Creates (overwrites) a copy of the pipeline parameters file.
    """
    backup_file = 'backup.'+configfile
    logger.info('Backing up {0} to {1}.'.format(configfile,backup_file))
    shutil.copyfile(configfile,backup_file)
    
def check_casalog(config,config_raw,logger):
    """
    Checks the casa log for severe errors.
    """
    casalogs = glob.glob('./casa*.log')
    casalogs.sort(key=os.path.getmtime)
    latest_log = open(casalogs[-1],'r')
    casalog_lines = latest_log.readlines()
    latest_log.close()
    sev_err = False
    for line in casalog_lines:
        if 'SEVERE' in line:
            if not sev_err:
                sev_err = True
                logger.critical('There were severe errors in the CASA log:')
            logger.critical(line)
    if sev_err:
        if config_raw.has_option('global','ignore_errs'):
            if not config['global']['ignore_errs']:
                sys.exit(-1)
        else:
            sys.exit(-1)
        
def check_casaversion(logger):
    """
    Checks the casa log for the version number.
    """
    casalogs = glob.glob('./casa*.log')
    casalogs.sort(key=os.path.getmtime)
    latest_log = open(casalogs[-1],'r')
    casalog_lines = latest_log.readlines()
    latest_log.close()
    for line in casalog_lines:
        if 'CASA Version' in line:
            inx = line.index('CASA Version')
            logger.info(line[inx:].rstrip())
            break