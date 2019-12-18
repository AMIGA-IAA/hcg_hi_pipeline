import time
import os
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
            logger.info('Deleted: {0}'.format(message, pathdir))
        except:
            logger.debug('Could not delete: {0}'.format(pathdir))
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
        
def listobs_sum(msfile, logger):
    """ 
    Write the listobs summary to file.
    
    Input:
    msfile = Path where the MS will be created. (String)
    """
    logger.info('Starting listobs summary.')
    sum_dir = './summary/'
    makedir(sum_dir)
    listobs_file = sum_dir+msfile+'.listobs.summary'
    rmdir(msfile)
    rmfile(listobs_file)
    logger.info('Writing listobs summary of data set to: {}'.format(listobs_file))
    listobs(vis=msfile, listfile=listobs_file)
    logger.info('Completed listobs summary.')


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

