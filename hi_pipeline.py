import time
import numpy
import shutil
import readline
import logging
import configparser
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
        logger.critical('configfile: {} not found'.format(configfile))
        sys.exit(-1)
    config_raw = configparser.RawConfigParser()
    config_raw.read(configfile)
    config = config_raw._sections
    for key in list(config.keys()):
        config[key].pop('__name__')
        for key2 in list(config[key].keys()):
            try:
                config[key][key2] = literal_eval(config[key][key2])
            except ValueError:
                pass
            except SyntaxError:
                pass
    return config,config_raw

# Utilities
def makedir(pathdir):
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

def rmdir(pathdir):
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


def rmfile(pathdir):
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
        return input(prompt)
    finally:
        readline.set_startup_hook()


# Set up the logger
def get_logger(    
        LOG_FORMAT     = '%(asctime)s | %(levelname)s | %(message)s',
        DATE_FORMAT    = '%Y-%m-%d %H:%M:%S',
        LOG_NAME       = 'logger',
        LOG_FILE_INFO  = 'mylog.log',
        LOG_FILE_ERROR = 'errors.log'):

    """ Set up a logger with UTC timestamps"""
    logger = logging.getLogger(LOG_NAME)
    log_formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
    logging.Formatter.converter = time.gmtime

    # comment this to suppress console output    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler) 

    # File mylog.log with all information
    file_handler_info = logging.FileHandler(LOG_FILE_INFO, mode='a+')
    file_handler_info.setFormatter(log_formatter)
    file_handler_info.setLevel(logging.INFO)
    logger.addHandler(file_handler_info)
    
    logger.setLevel(logging.INFO)
    return logger


def import_data(data_files, msfile):
    """ 
    Import VLA archive files from a location to a single MS.
    
    Input:
    data_files = Paths to the VLA archive files. (List/Array of Strings)
    msfile = Path where the MS will be created. (String)
    """
    logger.info('Starting import vla data')
    sum_dir = './summary/'
    makedir(sum_dir)
    listobs_file = sum_dir+msfile+'.listobs.summary'
    rmdir(msfile)
    rmfile(listobs_file)
    logger.info('Input files: {}'.format(data_files))
    logger.info('Output msfile: {}'.format(msfile))
    command = "importvla(archivefiles = {0}, vis = '{1}')".format(data_files, msfile)
    #importvla(archivefiles = data_files, vis = msfile)
    logger.info('Executing command: '+command)
    exec(command)
    listobs(vis=msfile, listfile=listobs_file)
    logger.info('Completed import vla data')


def get_obsfreq(msfile):
    """ 
    Returns freq of first and last channels, channel resolution and number of channels (first spw) in GHz.
    
    Input:
    msfile = Path to the MS. (String)
    
    Output:
    freq_ini = Start frequency. (Float)
    freq_end = Final frequency. (Float)
    chan_res = Channel width. (Float)
    nchan = Number of channels. (Integer)
    """
    msmd.open(msfile)
    nspw = msmd.nspw()
    freq_ini = msmd.chanfreqs(0)[0]/1e9
    freq_end = msmd.chanfreqs(nspw-1)[-1]/1e9
    chan_res = msmd.chanwidths(0)[0]/1e9
    nchan = len(msmd.chanwidths(0))
    msmd.done()
    return freq_ini, freq_end, chan_res, nchan

def find_mssources(msfile):
    """
    Extract source names from msfile metadata.
    Output format is a comma-separated string.
    
    Input:
    msfile = Path to the MS. (String)
    
    Output:
    mssources = All the fields observed in the MS separated by ','. (String)
    """
    msmd.open(msfile)
    mssources = ','.join(np.sort(msmd.fieldnames()))
    msmd.done()
    logger.info('Sources in MS {0}: {1}'.format(msfile, mssources))
    return mssources

def get_project(msfile):
    """
    Extract project code from msfile metadata.
    
    Input:
    msfile = Path to the MS. (String)
    
    Output:
    Project identifier. (String)
    """
    tb.open(msfile+'/OBSERVATION')
    project = tb.getcol('PROJECT')
    tb.close()
    return project[0]

def get_msinfo(msfile):
    """
    Extracts and prints basic information from the measurement set.
    
    Input:
    msfile = Path to the MS. (String)
    
    Output:
    msinfo = Summary of the the observations. (Ordered dictionary)
    """
    logger.info('Reading ms file information for MS: {0}'.format(msfile))
    msinfo = collections.OrderedDict()
    msinfo['msfile'] = msfile
    msinfo['project'] = get_project(msfile)
    msinfo['mssources'] = find_mssources(msfile)
    freq_ini, freq_end, chan_res, nchan = get_obsfreq(msfile)
    msinfo['freq_ini'] = freq_ini
    msinfo['freq_end'] = freq_end
    msinfo['chan_res'] = chan_res
    msinfo['nchan'] = nchan
    msinfo['num_spw'] = len(vishead(msfile, mode = 'list', listitems = ['spw_name'])['spw_name'][0])

    # Print summary
    logger.info('> Sources ({0}): {1}'.format(len(msinfo['mssources'].split(',')),
                                                 msinfo['mssources']))
    logger.info('> Number of spw: {0}'.format(msinfo['num_spw']))
    logger.info('> Channels per spw: {0}'.format(msinfo['nchan']))
    return msinfo


# Plotting
def plot_elevation(msfile,config):
    """
    Plots the elevation of the fields in each SPW as a function of time.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    logger.info('Starting plotting elevation.')
    plots_obs_dir = './plots/'
    makedir(plots_obs_dir)
    plot_file = plots_obs_dir+'{0}_elevation.png'.format(msfile)
    logger.info('Plotting elevation to: {}'.format(plot_file))
    elev = config['plot_elevation']
    avgtime = elev['avgtime']
    correlation = elev['correlation']
    width = elev['width']
    min_elev = elev['min_elev']
    max_elev = elev['max_elev']
    showgui = False
    plotms(vis=msfile, xaxis='time', yaxis='elevation',
            correlation=correlation, coloraxis = 'field',
            symbolsize=5, plotrange=[-1,-1, min_elev, max_elev],  
            averagedata=True, avgtime=str(avgtime), plotfile = plot_file,
            expformat = 'png', customsymbol = True, symbolshape = 'circle',
            overwrite=True, showlegend=False, showgui=showgui,
            exprange='all', iteraxis='spw')
    logger.info('Completed plotting elevation.')

def plot_ants(msfile):
    """
    Plots the layout of the antennae during the observations
    
    Input:
    msfile = Path to the MS. (String)
    """
    logger.info('Starting plotting antenna positions.')
    plots_obs_dir = './plots/'
    makedir(plots_obs_dir)
    plot_file = plots_obs_dir+'{0}_antpos.png'.format(msfile)
    logger.info('Plotting antenna positions to: {}'.format(plot_file))
    plotants(vis=msfile,figfile=plot_file)
    logger.info('Completed plotting antenna positions.')

def manual_flags():
    """
    Apply manual flags from the file 'manual_flags.py'.
    """
    logger.info('Starting manual flagging.')
    if interactive:
        print("\nManual flags from 'manual_flags.py' are about to be applied.")
        print("It is strongly recommended that you inspect the data and modify (and save) 'manual_flags.py' appropriately before proceeding.\n")
        resp = str(input('Do you want to proceed (y/n): '))
        while resp.lower() not in ['yes','ye','y']:
            resp = str(input('Do you want to proceed (y/n): '))
    logger.info('Applying flags from manual_flags.py')
    try:
        flag_file = open('manual_flags.py', 'r')
        if flag_file.readlines() == []:
            logger.warning("The file is empty. Continuing without manual flagging.")
        else:
            for command in flag_file.readlines():
                logger.info('Executing command: '+command)
                exec(command)
        flag_file.close()
        logger.info('Completed manual flagging.')
    except IOError:
        logger.warning("'manual_flags.py' does not exist. Continuing without manual flagging.")
        

def base_flags(msfile, config):
    """ 
    Sets basic initial data flags.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    logger.info('Starting basic flagging.')
    flag = config['flagging']
    tol = flag['shadow_tol'] 
    quack_int = flag['quack_int']
    #flag_version = 'base_flags'
    logger.info('Flagging antennae with more than {} m of shadowing.'.format(tol))
    command = "flagdata(vis='{0}', mode='shadow', tolerance={1}, flagbackup=False)".format(msfile,tol)
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Flagging zero amplitude data.')
    command = "flagdata(vis='{}', mode='clip', clipzeros=True, flagbackup=False)".format(msfile)
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Flagging first {} s of every scan.'.format(quack_int))
    command = "flagdata(vis='{0}', mode='quack', quackinterval={1}, quackmode='beg', flagbackup=False)".format(msfile,quack_int)
    logger.info('Executing command: '+command)
    exec(command)
    #logger.info('Saving flag version as: {}.'.format(flag_version))
    #command = "flagmanager(vis='{0}', mode='save', versionname='{1}')".format(msfile,flag_version)
    #logger.info('Executing command: '+command)
    #exec(command)
    logger.info('Completed basic flagging.')

def tfcrop(msfile):
    """
    Runs CASA's TFcrop flagging algorithm.
    
    Input:
    msfile = Path to the MS. (String)
    """
    #flag_version = 'tfcrop'
    logger.info('Starting running TFCrop.')
    command = "flagdata(vis='{}', mode='tfcrop', action='apply', display='', flagbackup=False)".format(msfile)
    logger.info('Executing command: '+command)
    exec(command)
    #logger.info('Saving flag version as: {}.'.format(flag_version))
    #command = "flagmanager(vis='{0}', mode='save', versionname='{1}')".format(msfile,flag_version)
    #logger.info('Executing command: '+command)
    #exec(command)
    logger.info('Completed running TFCrop.')

def rflag(msfile,config):
    """
    Runs CASA's rflag flagging algorithm.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    flag = config['flagging']
    #flag_version = 'rflag'
    thresh = flag['rthresh']
    logger.info('Starting running rflag with a threshold of {}.'.format(thresh))
    command = "flagdata(vis='{0}', mode='rflag', action='apply', datacolumn='corrected', freqdevscale={1}, timedevscale={1}, display='', flagbackup=False)".format(msfile,thresh)
    logger.info('Executing command: '+command)
    exec(command)
    #logger.info('Saving flag version as: {}.'.format(flag_version))
    #command = "flagmanager(vis='{0}', mode='save', versionname='{1}')".format(msfile,flag_version)
    #logger.info('Executing command: '+command)
    exec(command)
    logger.info('Completed running rflag.')

def extend_flags(msfile):
    """
    Extends existing flags.
    
    Input:
    msfile = Path to the MS. (String)
    """
    flag_version = 'extended'
    logger.info('Starting extending existing flags.')
    command = "flagdata(vis='{}', mode='extend', spw='', extendpols=True, action='apply', display='', flagbackup=False)".format(msfile)
    logger.info('Executing command: '+command)
    exec(command)
    command = "flagdata(vis='{}', mode='extend', spw='', growtime=75.0, growfreq=90.0, action='apply', display='', flagbackup=False)".format(msfile)
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Completed extending existing flags.')

def flag_sum(msfile,name):
    """
    Writes a summary of the current flags to file.
    
    Input:
    msfile = Path to the MS. (String)
    name = Root of filename where flags summary will be saved. (String) 
    """
    sum_dir = './summary/'
    makedir(sum_dir)
    out_file = sum_dir+'{0}.{1}flags.summary'.format(msfile,name)
    logger.info('Starting writing flag summary to: {}.'.format(out_file))
    flag_info = flagdata(vis=msfile, mode='summary')
    out_file = open(out_file, 'w')
    out_file.write('Total flagged data: {:.2%}\n\n'.format(flag_info['flagged']/flag_info['total']))
    logger.info('Total flagged data: {:.2%}'.format(flag_info['flagged']/flag_info['total']))
    out_file.write('Flagging per spectral window\n')
    for spw in list(flag_info['spw'].keys()):
        out_file.write('SPW {0}: {1:.2%}\n'.format(spw,flag_info['spw'][spw]['flagged']/flag_info['spw'][spw]['total']))
    out_file.write('\nFlagging per field\n')
    for field in list(flag_info['field'].keys()):
        out_file.write('{0}: {1:.2%}\n'.format(field,flag_info['field'][field]['flagged']/flag_info['field'][field]['total']))
    out_file.write('\nFlagging per antenna\n')
    for ant in list(flag_info['antenna'].keys()):
        out_file.write('{0}: {1:.2%}\n'.format(ant,flag_info['antenna'][ant]['flagged']/flag_info['antenna'][ant]['total']))
    out_file.close()
    logger.info('Completed writing flag summary.')
    
def restore_flags(msfile,name):
    """
    Restored the flag version corresponding to the named file.
    
    Input:
    msfile = Path to the MS. (String)
    name = Root of filename for the flag version. (String) 
    """
    logger.info('Restoring flag version from: {}.'.format(name))
    command = "flagmanager(vis='{0}', mode='restore', versionname='{1}')".format(msfile,name)
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Completed restoring flag version.')
    
def save_flags(msfile,name):
    """
    Save the current flag version as "name".
    
    Input:
    msfile = Path to the MS. (String)
    name = Root of filename for the flag version. (String) 
    """
    logger.info('Saving flag version as: {}.'.format(name))
    command = "flagmanager(vis='{0}', mode='save', versionname='{1}')".format(msfile,name)
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Completed saving flag version.')
    

def select_refant(msfile,config,config_raw,config_file):
    """
    Checks if a reference antenna is set, if it has not been then the user is queried to set it.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    config_raw = The instance of the parser.
    config_file = Path to configuration file. (String)
    """
    logger.info('Starting reference antenna selection.')
    calib = config['calibration']
    tb.open(msfile+'/ANTENNA')
    ant_names = tb.getcol('NAME')
    tb.close()
    if calib['refant'] not in ant_names:
        logger.warning('No valid reference antenna set. Requesting user input.')
        first = 0
        print('\n\n\n')
        while calib['refant'] not in ant_names:
            if first > 0:
                print('\n\nString entered is not a valid antenna name.')
            print(('Valid antenna names:\n{}\n'.format(ant_names)))
            calib['refant'] = str(input('Please select a reference antenna by name: '))
            first += 1
        logger.info('Updating config file ({0}) to set reference antenna as {1}.'.format(config_file,calib['refant']))
        config_raw.set('calibration','refant',calib['refant'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
        logger.info('Completed reference antenna selection.')
    else:
        logger.info('Reference antenna already set as: {}.'.format(calib['refant']))

def set_fields(msfile,config,config_raw,config_file):
    """
    Checks if the field intentions have already been set, if not then the user is queried.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    config_raw = The instance of the parser.
    config_file = Path to configuration file. (String)
    """
    logger.info('Starting set field purposes.')
    calib = config['calibration']
    tb.open(msfile+'/FIELD')
    field_names = tb.getcol('NAME')
    tb.close()
    tb.open('{}/SPECTRAL_WINDOW'.format(msfile))
    spw_names = tb.getcol('NAME')
    spw_IDs = tb.getcol('DOPPLER_ID')
    nspw = len(spw_IDs)
    tb.close()
    std_flux_mods = ['3C48_L.im', '3C138_L.im', '3C286_L.im']
    std_flux_names = {'0134+329': '3C48_L.im', '0137+331': '3C48_L.im', '3C48': '3C48_L.im',
                      '0518+165': '3C138_L.im', '0521+166': '3C138_L.im', '3C138': '3C138_L.im',
                      '1328+307': '3C286_L.im', '1331+305': '3C286_L.im', '3C286': '3C286_L.im'}
    
    change_made = False
    if len(calib['targets']) == 0:
        if not interactive:
            logger.critical('There are no targets listed in the parameters file.')
            sys.exit(-1)
        else:
            logger.warning('No target field(s) set. Requesting user input.')
            print('\n\n')
            while True:
                target = ''
                print(('Valid field names:\n{}\n'.format(field_names)))
                target = str(input('Please select a target field by name: '))
                if target not in field_names:
                    print('\n\nString entered is not a valid field name.')
                    continue
                else:
                    calib['targets'].append(target)
                    logger.info('{} set as a target field.'.format(target))
                    resp = ''
                    while (resp.lower() not in ['yes','ye','y']) and (resp.lower() not in ['no','n']) :
                        resp = str(input('Do you want to add another target (y/n): '))
                    if resp.lower() in ['yes','ye','y']:
                        continue
                    else:
                        break
            change_made = True
    else:
        logger.info('Target field(s) already set as: {}.'.format(calib['targets']))
        if interactive:
            resp = str(input('Do you want to add another target (y/n): '))
            while (resp.lower() not in ['yes','ye','y']) and (resp.lower() not in ['no','n']) :
                resp = str(input('Do you want to add another target (y/n): '))
            if resp.lower() in ['yes','ye','y']:
                while True:
                    target = ''
                    print(('Valid field names:\n{}\n'.format(field_names)))
                    target = str(input('Please select a target field by name: '))
                    if target not in field_names:
                        print('\n\nString entered is not a valid field name.')
                        continue
                    else:
                        calib['targets'].append(target)
                        logger.info('{} set as a target field.'.format(target))
                        resp = ''
                        while (resp.lower() not in ['yes','ye','y']) and (resp.lower() not in ['no','n']) :
                            resp = str(input('Do you want to add another target (y/n): '))
                        if resp.lower() in ['yes','ye','y']:
                            continue
                        else:
                            break
                change_made = True
        
    flux_cal_names_bad = False
    for i in range(len(calib['fluxcal'])):
        if calib['fluxcal'][i] not in field_names:
            flux_cal_names_bad = True
            if not interactive:
                logger.critical('Illegal name for flux calibrator: {}'.format(calib['fluxcal'][i]))
                sys.exit(-1)
    if flux_cal_names_bad or len(calib['fluxcal']) != nspw:
        if nspw == 1:
            if not interactive:
                logger.critical('No valid flux calibrator set.')
                sys.exit(-1)
            else:
                logger.warning('No valid flux calibrator set. Requesting user input.')
                while calib['fluxcal'][0] not in field_names:
                    if first > 0:
                        print('\n\nString entered is not a valid field name.')
                    print(('Valid field names:\n{}\n'.format(field_names)))
                    calib['fluxcal'][0] = str(input('Please select a flux calibrator by name: '))
                    first += 1
                change_made = True
        else:
            if not interactive:
                logger.critical('The number of flux calibrators does not match the number of spectral windows ({}).'.format(nspw))
                logger.info('Flux calibrators: {}'.format(calib['fluxcal']))
                sys.exit(-1)
            else:
                if len(calib['fluxcal']) != nspw:
                    logger.warning('Incorrect number of flux calibrators set. Requesting user input.')
                else:
                    logger.warning('At least one flux calibrator is incorrect. Please revise the list.')
                logger.info('Current calibrators list: {}'.format(calib['fluxcal']))
                if len(calib['fluxcal']) > nspw:
                    logger.warning('Too many flux calibrators set.')
                    logger.warning('The following will be truncated: {}'.format(calib['fluxcal'][nspw-1:]))
                    calib['fluxcal'] = calib['fluxcal'][:nspw]
                if len(calib['fluxcal']) < nspw:
                    logger.warning('Too few flux calibrators set.')
                    for i in range(len(calib['fluxcal']),nspw):
                        calib['fluxcal'].append('')
                i = 0
                first = True
                print(('Valid field names:\n{}\n'.format(field_names)))
                while i in range(len(calib['fluxcal'])):
                    if first:
                        print(('SPW {0}: {1}'.format(spw_IDs[i],spw_names[i])))
                    calib['fluxcal'][i] = uinput('Enter flux calibrator for SPW {}: '.format(spw_IDs[i], default=calib['fluxcal'][i]))
                    if calib['fluxcal'][i] not in field_names:
                        print('\n\nString entered is not a valid field name.')
                        print(('Valid field names:\n{}\n'.format(field_names)))
                        first = False
                    else:
                        i += 1
                        first = True
                change_made = True
        logger.info('Flux calibrators set as: {}.'.format(calib['fluxcal']))
    else:
        logger.info('Flux calibrator already set as: {}.'.format(calib['fluxcal']))
        
    
    
    flux_mod_names_bad = False
    for i in range(len(calib['fluxmod'])):
        if calib['fluxmod'][i] not in std_flux_mods:
            flux_mod_names_bad = True
            if not interactive:
                logger.error('Non-standard name for flux model: {}'.format(calib['fluxmod'][i]))
    if flux_mod_names_bad or len(calib['fluxmod']) != len(calib['fluxcal']):
        logger.warning('Flux calibrator models do not match flux calibrators.')
    else:
        logger.info('Flux models already set as: {}.'.format(calib['fluxmod']))
            
    if len(calib['fluxmod']) == 0:
        if not interactive:
            logger.warning('There is no flux calibrator model listed in the parameters file.')
        flux_mod_names_bad = False
        for i in range(len(calib['fluxcal'])):
            if calib['fluxcal'][i] in list(std_flux_names.keys()):
                calib['fluxmod'].append(std_flux_names[calib['fluxcal'][i]])
            else:
                flux_mod_names_bad = True
                if not interactive:
                    logger.critical('Some flux calibrator models cannot be automatcially assigned.')
                    sys.exit(-1)
        if not flux_mod_names_bad:
            logger.info('Flux models automatically set as: {}.'.format(calib['fluxmod']))
            change_made = True
                
    if flux_mod_names_bad or len(calib['fluxmod']) != len(calib['fluxcal']):
        if not interactive:
            logger.critical('The number of models does not match the number of flux calibrators.')
            logger.info('Flux calibrators: {}'.format(calib['fluxcal']))
            logger.info('Flux calibrator models: {}'.format(calib['fluxmod']))
            sys.exit(-1)
        else:
            if len(calib['fluxcal']) == 1:
                logger.warning('No valid flux model set. Requesting user input.')
                while calib['fluxmod'][0] not in std_flux_mods:
                    print('Usual flux calibrator models will be 3C48_L.im, 3C138_L.im, or 3C286_L.im.\n')
                    calib['fluxmod'][0] = str(input('Please select a flux model name: '))
                    if calib['fluxmod'][0] not in std_flux_mods:
                        resp = str(input('The model name provided is not one of the 3 expected options.\nDo you want to proceed with the model {} ?'.format(calib['fluxmod'][0])))
                        if resp.lower() not in ['yes','ye','y']:
                            break
                        else:
                            continue
            else:
                if len(calib['fluxmod']) != len(calib['fluxcal']):
                    logger.warning('Incorrect number of flux models set. Requesting user input.')
                else:
                    logger.warning('At least one flux model is incorrect. Please revise the list.')
                logger.info('Current models list: {}'.format(calib['fluxmod']))
                if len(calib['fluxmod']) > len(calib['fluxcal']):
                    logger.warning('Too many flux models set.')
                    logger.warning('The following will be truncated: {}'.format(calib['fluxmod'][len(calib['fluxcal'])-1:]))
                    calib['fluxmod'] = calib['fluxmod'][:len(calib['fluxcal'])]
                if len(calib['fluxmod']) < len(calib['fluxcal']):
                    logger.warning('Too few flux models set.')
                    for i in range(len(calib['fluxmod']),len(calib['fluxcal'])):
                        calib['fluxmod'].append('')
                i = 0
                while i in range(len(calib['fluxmod'])):
                    print('Usual flux calibrator models will be 3C48_L.im, 3C138_L.im, or 3C286_L.im.\n')
                    calib['fluxmod'][i] = uinput('Enter flux model for calibrator {}: '.format(calib['fluxcal'][i], default=calib['fluxmod'][i]))
                    if calib['fluxmod'][i] not in std_flux_mods:
                        resp = str(input('The model name provided is not one of the 3 expected options.\nDo you want to proceed with the model {} ?'.format(calib['fluxmod'][i])))
                        if resp.lower() in ['yes','ye','y']:
                            i += 1
                    else:
                        i += 1
            change_made = True
        logger.info('Flux models set as: {}.'.format(calib['fluxmod']))
        
    
    band_cal_names_bad = False
    for i in range(len(calib['bandcal'])):
        if calib['bandcal'][i] not in field_names:
            band_cal_names_bad = True
            if not interactive:
                logger.critical('Illegal name for bandpass calibrator: {}'.format(calib['bandcal'][i]))
                sys.exit(-1)
    if band_cal_names_bad or len(calib['bandcal']) != nspw:
        if nspw == 1:
            if not interactive:
                logger.critical('No valid bandpass calibrator set.')
                sys.exit(-1)
            else:
                logger.warning('No valid bandpass calibrator set. Requesting user input.')
                while calib['bandcal'][0] not in field_names:
                    if first > 0:
                        print('\n\nString entered is not a valid field name.')
                    print(('Valid field names:\n{}\n'.format(field_names)))
                    calib['bandcal'][0] = str(input('Please select a bandpass calibrator by name: '))
                    first += 1
                change_made = True
        else:
            if not interactive:
                logger.critical('The number of bandpass calibrators does not match the number of spectral windows ({}).'.format(nspw))
                logger.info('Bandpass calibrators: {}'.format(calib['bandcal']))
                sys.exit(-1)
            else:
                if len(calib['bandcal']) != nspw:
                    logger.warning('Incorrect number of bandpass calibrators set. Requesting user input.')
                else:
                    logger.warning('At least one bandpass calibrator is incorrect. Please revise the list.')
                logger.info('Current calibrators list: {}'.format(calib['bandcal']))
                if len(calib['bandcal']) > nspw:
                    logger.warning('Too many bandpass calibrators set.')
                    logger.warning('The following will be truncated: {}'.format(calib['bandcal'][nspw-1:]))
                    calib['bandcal'] = calib['bandcal'][:nspw]
                if len(calib['bandcal']) < nspw:
                    logger.warning('Too few bandpass calibrators set.')
                    for i in range(len(calib['bandcal']),nspw):
                        calib['bandcal'].append('')
                i = 0
                first = True
                print(('Valid field names:\n{}\n'.format(field_names)))
                while i in range(len(calib['bandcal'])):
                    if first:
                        print(('SPW {0}: {1}'.format(spw_IDs[i],spw_names[i])))
                    calib['bandcal'][i] = uinput('Enter bandpass calibrator for SPW {}: '.format(spw_IDs[i], default=calib['bandcal'][i]))
                    if calib['bandcal'][i] not in field_names:
                        print('\n\nString entered is not a valid field name.')
                        print(('Valid field names:\n{}\n'.format(field_names)))
                        first = False
                    else:
                        i += 1
                        first = True
                change_made = True
        logger.info('Bandpass calibrators set as: {}.'.format(calib['bandcal']))
    else:
        logger.info('Bandpass calibrator already set as: {}.'.format(calib['bandcal']))
        

    phase_cal_names_bad = False
    for i in range(len(calib['phasecal'])):
        if calib['phasecal'][i] not in field_names:
            phase_cal_names_bad = True
            if not interactive:
                logger.critical('Illegal name for phase calibrator: {}'.format(calib['phasecal'][i]))
                sys.exit(-1)
    if phase_cal_names_bad or len(calib['phasecal']) != len(calib['targets']):
        if len(calib['targets']) == 1:
            if not interactive:
                logger.critical('No valid phase calibrator set.')
                sys.exit(-1)
            else:
                logger.warning('No valid phase calibrator set. Requesting user input.')
                while calib['phasecal'][0] not in field_names:
                    if first > 0:
                        print('\n\nString entered is not a valid field name.')
                    print(('Valid field names:\n{}\n'.format(field_names)))
                    calib['phasecal'][0] = str(input('Please select a phase calibrator by name: '))
                    first += 1
                change_made = True
        else:
            if not interactive:
                logger.critical('The number of phase calibrators does not match the number of targets.')
                logger.info('Phase calibrators: {}'.format(calib['phasecal']))
                logger.info('Targets: {}'.format(calib['targets']))
                sys.exit(-1)
            else:
                if len(calib['phasecal']) != len(calib['targets']):
                    logger.warning('Incorrect number of phase calibrators set. Requesting user input.')
                else:
                    logger.warning('At least one phase calibrator is incorrect. Please revise the list.')
                logger.info('Current calibrators list: {}'.format(calib['phasecal']))
                if len(calib['phasecal']) > len(calib['targets']):
                    logger.warning('Too many phase calibrators set.')
                    logger.warning('The following will be truncated: {}'.format(calib['phasecal'][len(calib['targets'])-1:]))
                    calib['phasecal'] = calib['phasecal'][:len(calib['targets'])]
                if len(calib['phasecal']) < len(calib['targets']):
                    logger.warning('Too few phase calibrators set.')
                    for i in range(len(calib['phasecal']),len(calib['targets'])):
                        calib['phasecal'].append('')
                i = 0
                print(('Valid field names:\n{}\n'.format(field_names)))
                while i in range(len(calib['phasecal'])):
                    calib['phasecal'][i] = uinput('Enter phase calibrator for {}: '.format(calib['targets'][i]), default=calib['phasecal'][i])
                    if calib['phasecal'][i] not in field_names:
                        print('\n\nString entered is not a valid field name.')
                        print(('Valid field names:\n{}\n'.format(field_names)))
                    else:
                        i += 1
                change_made = True
        logger.info('Phase calibrators set as: {}.'.format(calib['phasecal']))
    else:
        logger.info('Phase calibrator already set as: {}.'.format(calib['phasecal']))
    if change_made:
        logger.info('Updating config file to set target and calibrator fields.')
        config_raw.set('calibration','fluxcal',calib['fluxcal'])
        config_raw.set('calibration','bandcal',calib['bandcal'])
        config_raw.set('calibration','phasecal',calib['phasecal'])
        config_raw.set('calibration','targets',calib['targets'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    else:
        logger.info('No changes made to preset target and calibrator fields.')
    logger.info('Completed setting field purposes.')

   
    
def calibration(msfile,config):
    """
    Runs the basic calibration steps on each SPW based on the intents described in the configuration file.
    Applies the calibration to all science target fields.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    logger.info('Starting calibration.')
    plots_obs_dir = './plots/'
    makedir(plots_obs_dir)
    sum_dir = './summary/'
    makedir(sum_dir)
    cal_tabs = './cal_tabs/'
    makedir(cal_tabs)
    calib = config['calibration']
    
    tb.open('{}/SPECTRAL_WINDOW'.format(msfile))
    spw_names = list(tb.getcol('NAME'))
    spw_IDs = list(tb.getcol('DOPPLER_ID'))
    nspw = len(spw_names)
    tb.close()
    
    gctab = cal_tabs+'gaincurve.cal'
    logger.info('Calibrating gain vs elevation({}).'.format(gctab))
    command = "gencal(vis='{0}', caltable='{1}', caltype='gceff')".format(msfile,gctab)
    logger.info('Executing command: '+command)
    exec(command)
    
    for i in range(nspw):
        msmd.open(msfile)
        spw_fields = msmd.fieldsforspw(spw_IDs[i], asnames=True)
        msmd.close()
        
        logger.info('Beginning calibration of SPW {}.'.format(spw_IDs[i]))
        
        logger.info('Load model for flux calibrator {0} ({1}).'.format(calib['fluxcal'][i],calib['fluxmod'][i]))
        command = "setjy(vis='{0}', field='{1}', spw='{2}', scalebychan=True, model='{3}')".format(msfile,calib['fluxcal'][i],spw_IDs[i],calib['fluxmod'][i])
        logger.info('Executing command: '+command)
        exec(command)

        plot_file = plots_obs_dir+'{0}_bpphaseint_spw{1}.png'.format(msfile,spw_IDs[i])
        logger.info('Plotting bandpass phase vs. time for reference antenna to: {}'.format(plot_file))
        plotms(vis=msfile, plotfile=plot_file, xaxis='channel', yaxis='phase', field=calib['bandcal'][i], spw = str(spw_IDs[i]), correlation='RR,LL', avgtime='1E10', antenna=calib['refant'], coloraxis='antenna2', expformat='png', overwrite=True, showlegend=False, showgui=False)

        dltab = cal_tabs+'delays_spw{}.cal'.format(spw_IDs[i])
        logger.info('Calibrating delays for bandpass calibrator {0} ({1}).'.format(calib['bandcal'][i],dltab))
        command = "gaincal(vis='{0}', field='{1}', spw='{2}', caltable='{3}', refant='{4}', gaintype='K', gaintable=['{5}'])".format(msfile,calib['bandcal'][i],spw_IDs[i],dltab,calib['refant'],gctab)
        logger.info('Executing command: '+command)
        exec(command)

        bptab = cal_tabs+'bpphase_spw{}.gcal'.format(spw_IDs[i])
        logger.info('Make bandpass calibrator phase solutions for {0} ({1}).'.format(calib['bandcal'][i],bptab))
        command = "gaincal(vis='{0}', field='{1}',  spw='{2}', caltable='{3}', refant='{4}', calmode='p', solint='int', combine='', minsnr=2.0, gaintable=['{5}','{6}'])".format(msfile,calib['bandcal'][i],spw_IDs[i],bptab,calib['refant'],gctab,dltab)
        logger.info('Executing command: '+command)
        exec(command)

        plot_file = plots_obs_dir+'{0}_bpphasesol_spw{1}.png'.format(msfile,spw_IDs[i])
        logger.info('Plotting bandpass phase solutions to: {}'.format(plot_file))
        plotms(vis=bptab, plotfile=plot_file, gridrows=3, gridcols=3, xaxis='time', yaxis='phase',
               plotrange=[0,0,-180,180], expformat='png', overwrite=True, showlegend=False, showgui=False, exprange='all',
               iteraxis='antenna', spw=str(spw_IDs[i]))

        bstab = cal_tabs+'bandpass_spw{}.bcal'.format(spw_IDs[i])
        logger.info('Determining bandpass solution ({}).'.format(bstab))
        command = "bandpass(vis='{0}', caltable='{1}', field='{2}', spw='{3}', refant='{4}', solint='inf', solnorm=True, gaintable=['{5}', '{6}', '{7}'])".format(msfile,bstab,calib['bandcal'][i],spw_IDs[i],calib['refant'],gctab, dltab, bptab)
        logger.info('Executing command: '+command)
        exec(command)

        plot_file = plots_obs_dir+'{0}_bandpasssol_spw{1}.png'.format(msfile,spw_IDs[i])
        logger.info('Plotting bandpass amplitude solutions to: {}'.format(plot_file))
        plotms(vis=bstab, plotfile=plot_file, gridrows=3, gridcols=3, xaxis='chan', yaxis='amp',
               expformat='png', overwrite=True, showlegend=False, showgui=False, exprange='all',
               iteraxis='antenna', coloraxis='corr', spw=str(spw_IDs[i]))
        
        calfields = []
        for field in calib['fluxcal']:
            if field in spw_fields:
                calfields.append(field)
        for field in calib['bandcal']:
            if field in spw_fields:
                calfields.append(field)
        for field in calib['phasecal']:
            if field in spw_fields:
                calfields.append(field)
        calfields = list(set(calfields))
        calfields = ','.join(calfields)
    
        iptab = cal_tabs+'intphase_spw{}.gcal'.format(spw_IDs[i])
        logger.info('Determining integration phase solutions ({}).'.format(iptab))
        command = "gaincal(vis='{0}', field='{1}', spw='{2}', caltable='{3}', refant='{4}', calmode='p', solint='int', minsnr=2.0, gaintable=['{5}', '{6}', '{7}'])".format(msfile,calfields,spw_IDs[i],iptab,calib['refant'],gctab, dltab, bstab)
        logger.info('Executing command: '+command)
        exec(command)
        
        sptab = cal_tabs+'scanphase_spw{}.gcal'.format(spw_IDs[i])
        logger.info('Determining scan phase solutions ({}).'.format(sptab))
        command = "gaincal(vis='{0}', field='{1}', spw='{2}', caltable='{3}', refant='{4}', calmode='p', solint='inf', minsnr=2.0, gaintable=['{5}', '{6}', '{7}'])".format(msfile,calfields,spw_IDs[i],sptab,calib['refant'],gctab, dltab, bstab)
        logger.info('Executing command: '+command)
        exec(command)
        
        amtab = cal_tabs+'amp_spw{}.gcal'.format(spw_IDs[i])
        logger.info('Determining amplitude solutions ({}).'.format(amtab))
        command = "gaincal(vis='{0}', field='{1}', spw='{2}', caltable='{3}', refant='{4}', calmode='ap', solint='inf', minsnr=2.0, gaintable=['{5}', '{6}', '{7}', '{8}'])".format(msfile,calfields,spw_IDs[i],amtab,calib['refant'],gctab, dltab, bstab, iptab)
        logger.info('Executing command: '+command)
        exec(command)
        
        plot_file = plots_obs_dir+'phasesol_spw{0}.png'.format(spw_IDs[i])
        logger.info('Plotting phase solutions to: {}'.format(plot_file))
        plotms(vis=amtab, plotfile=plot_file, gridrows=3, gridcols=3, xaxis='time', yaxis='phase',
               expformat='png', overwrite=True, showlegend=False, showgui=False, exprange='all',
               iteraxis='antenna', coloraxis='corr', plotrange=[-1,-1,-20,20])

        plot_file = plots_obs_dir+'ampsol_spw{0}.png'.format(spw_IDs[i])
        logger.info('Plotting amplitude solutions to: {}'.format(plot_file))
        plotms(vis=amtab, plotfile=plot_file, gridrows=3, gridcols=3, xaxis='time', yaxis='amp',
               expformat='png', overwrite=True, showlegend=False, showgui=False, exprange='all',
               iteraxis='antenna', coloraxis='corr', plotrange=[-1,-1,0,1])
        
        fxtab = cal_tabs+'fluxsol_spw{}.cal'.format(spw_IDs[i])
        logger.info('Applying flux scale to calibrators ({}).'.format(fxtab))
        command = "fluxscale(vis='{0}', caltable='{1}', fluxtable='{2}', reference='{3}', incremental=True)".format(msfile,amtab,fxtab,calib['fluxcal'][i])
        logger.info('Executing command: flux_info = '+command)
        exec('flux_info = '+command)
        
        out_file = sum_dir+'{0}.flux.summary'.format(msfile)
        logger.info('Writing calibrator fluxes summary to: {}.'.format(out_file))
        out_file = open(out_file, 'a+')
        out_file.write('Spectral window: {}\n'.format(spw_IDs[i]))
        for k in range(len(list(flux_info.keys()))):
            if 'spw' in list(flux_info.keys())[k] or 'freq' in list(flux_info.keys())[k]:
                continue
            else:
                fieldID = list(flux_info.keys())[k]
                out_file.write('Flux density for {0}: {1} +/- {2} Jy\n'.format(flux_info[fieldID]['fieldName'], flux_info[fieldID][str(spw_IDs[i])]['fluxd'][0], flux_info[fieldID][str(spw_IDs[i])]['fluxdErr'][0]))
                out_file.write('\n')
        out_file.close()
        
        logger.info('Apply all calibrations to bandpass and flux calibrators in SPW {}.'.format(spw_IDs[i]))
        logger.info('Applying clibration to: {}'.format(calib['bandcal'][i]))
        command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}', '{7}'], gainfield=['', '{1}', '{1}', '{1}', '{1}', '{1}'], calwt=False)".format(msfile,calib['bandcal'][i],gctab, dltab, bstab, iptab, amtab, fxtab)
        logger.info('Executing command: '+command)
        exec(command)
        if calib['fluxcal'][i] != calib['bandcal'][i]:
            logger.info('Applying clibration to: {}'.format(calib['fluxcal'][i]))
            command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}', '{7}'], gainfield=['', '{8}', '{8}', '{1}', '{1}', '{1}'], calwt=False)".format(msfile,calib['fluxcal'][i],gctab, dltab, bstab, iptab, amtab, fxtab,calib['bandcal'][i])
            logger.info('Executing command: '+command)
            exec(command)
            
        plot_file = plots_obs_dir+'corr_phase_spw{}.png'.format(spw_IDs[i])
        logger.info('Plotting corrected phases for {0} to: {1}'.format(calib['bandcal'][i],plot_file))
        plotms(vis=msfile, plotfile=plot_file, field=calib['bandcal'][i], xaxis='channel', yaxis='phase', ydatacolumn='corrected', correlation='RR,LL', avgtime='1E10', antenna=calib['refant'], spw=spw_IDs[i], coloraxis='antenna2', expformat='png', overwrite=True, showlegend=False, showgui=False)

        plot_file = plots_obs_dir+'corr_amp_spw{}.png'.format(spw_IDs[i])
        logger.info('Plotting corrected amplitudes for {0} to: {1}'.format(calib['bandcal'][i],plot_file))
        plotms(vis=msfile, plotfile=plot_file, field=calib['bandcal'][i], xaxis='channel', yaxis='amp', ydatacolumn='corrected', correlation='RR,LL', avgtime='1E10', antenna=calib['refant'], spw=spw_IDs[i], coloraxis='antenna2', expformat='png', overwrite=True, showlegend=False, showgui=False)
            
            
    for target in calib['targets']:
        inx = calib['targets'].index(target)
        phasecal = calib['phasecal'][inx]
        logger.info('Applying clibration to: {0} and {1}'.format(target,phasecal))
        msmd.open(msfile)
        spws = msmd.spwsforfield(target)
        msmd.close()
        logger.info('{0} was observed in SPW(s): {1}'.format(target,spws))
        
        for spw in spws:
            i = spw_IDs.index(spw)
            dltab = cal_tabs+'delays_spw{}.cal'.format(spw_IDs[i])
            bptab = cal_tabs+'bpphase_spw{}.gcal'.format(spw_IDs[i])
            bstab = cal_tabs+'bandpass_spw{}.bcal'.format(spw_IDs[i])
            iptab = cal_tabs+'intphase_spw{}.gcal'.format(spw_IDs[i])
            sptab = cal_tabs+'scanphase_spw{}.gcal'.format(spw_IDs[i])
            amtab = cal_tabs+'amp_spw{}.gcal'.format(spw_IDs[i])
            fxtab = cal_tabs+'fluxsol_spw{}.cal'.format(spw_IDs[i])
            
            logger.info('Apply applying calibrations in SPW: {}'.format(spw))
            logger.info('Applying clibration to: {}'.format(phasecal))
            command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}', '{7}'], gainfield=['', '{8}', '{8}', '{1}', '{1}', '{1}'], calwt=False)".format(msfile,phasecal,gctab, dltab, bstab, iptab, amtab, fxtab,calib['bandcal'][i])
            logger.info('Executing command: '+command)
            exec(command)
            
            logger.info('Applying clibration to: {}'.format(target))
            command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}', '{7}'], gainfield=['', '{8}', '{8}', '{9}', '{9}', '{9}'], calwt=False)".format(msfile,target,gctab, dltab, bstab, iptab, amtab, fxtab,calib['bandcal'][i],phasecal)
            logger.info('Executing command: '+command)
            exec(command)
    logger.info('Completed calibration.')



def split_fields(msfile,config):
    """
    Splits the MS into separate MS for each science target.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    logger.info('Starting split fields.')
    calib = config['calibration']
    src_dir = config['global']['src_dir']+'/'
    makedir('./'+src_dir)
    for field in calib['targets']:
        logger.info('Splitting {0} into separate file: {1}.'.format(field, field+'.split'))
        command = "split(vis='{0}', outputvis='{1}{2}'+'.split', field='{2}')".format(msfile,src_dir,field)
        logger.info('Executing command: '+command)
        exec(command)
    logger.info('Completed split fields.')
    

        
def contsub(msfile,config,config_raw,config_file):
    """
    Subtracts the continuum from each of the science target MSs.
    If the no line free range is set then the user is queried (in interactive mode) and the configuration file updated.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    config_raw = The instance of the parser.
    config_file = Path to configuration file. (String)
    """
    logger.info('Starting continuum subtraction.')
    contsub = config['continuum_subtraction']
    calib = config['calibration']
    src_dir = config['global']['src_dir']+'/'
    logger.info('Checking for line free channel ranges in parameters.')
    reset_ch = False
    if len(contsub['linefree_ch']) == 0 or len(contsub['linefree_ch']) != len(calib['targets']):
        reset_ch = True
        if len(contsub['linefree_ch']) < len(calib['targets']):
            logger.warning('There are more target fields than channel ranges. Appending blank ranges.')
            while len(contsub['linefree_ch']) < len(calib['targets']):
                contsub['linefree_ch'].append('')
        elif len(contsub['linefree_ch']) > len(calib['targets']):
            logger.warning('There are more channel ranges than target fields.')
            logger.info('Current channel ranges: {}'.format(contsub['linefree_ch']))
            logger.warning('The channel range list will now be truncated to match the number of targets.')
            contsub['linefree_ch'] = contsub['linefree_ch'][:len(calib['targets'])]
    elif interactive:
        print('Current line free channels set as:')
        for i in range(len(contsub['linefree_ch'])):
            print(('{0}: {1}'.format(calib['targets'][i],contsub['linefree_ch'][i])))
        resp = str(input('Do you want revise the line free channels (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_ch = True
    if reset_ch:
        if not interactive:
            logger.critical('The number of line free channel ranges provided does not match the number of targets.')
            logger.info('Line free change ranges: {}'.format(contsub['linefree_ch']))
            logger.info('Targets: {}'.format(calib['targets']))
            sys.exit(-1)
        else:
            print('For each target enter the line free channels in the following format:\nspwID1:min_ch1~max_ch1;min_ch2~max_ch2,spwID2:min_ch3~max_ch3 etc.')
            for i in range(len(calib['targets'])):
                contsub['linefree_ch'][i] = uinput('Line free channels for {}: '.format(calib['targets'][i]), contsub['linefree_ch'][i])
                logger.info('Setting line free channels for {0} as: {1}.'.format(calib['targets'][i], contsub['linefree_ch'][i]))
            logger.info('Updating config file to set line free channels.')
            config_raw.set('continuum_subtraction','linefree_ch',contsub['linefree_ch'])
            configfile = open(config_file,'w')
            config_raw.write(configfile)
            configfile.close()
    logger.info('Line free channels set as: {}.'.format(contsub['linefree_ch']))
    logger.info('For the targets: {}.'.format(calib['targets']))
    for i in range(len(calib['targets'])):
        target = calib['targets'][i]
        chans = contsub['linefree_ch'][i]
        spws = chans.split(',')
        for i in range(len(spws)):
            spw = spws[i].strip()
            spw = spw[0]
            spws[i] = spw
        logger.info('Subtracting the continuum from field: {}'.format(target))
        command = "uvcontsub(vis='{0}{1}'+'.split', field='{1}', fitspw='{2}', spw='{3}', excludechans=False,combine='',solint='int', fitorder={4}, want_cont={5})".format(src_dir,target,chans,','.join(spws),contsub['fitorder'],contsub['save_cont'])
        logger.info('Executing command: '+command)
        exec(command)
    logger.info('Completed continuum subtraction.')
    


def plot_spec(config):
    """
    For each SPW and each science target amplitude vs channel and amplitude vs velocity are plotted.
    
    Input:
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    logger.info('Starting plotting amplitude spectrum.')
    plots_obs_dir = './plots/'
    makedir(plots_obs_dir)
    calib = config['calibration']
    targets = calib['targets']
    src_dir = config['global']['src_dir']+'/'
    for target in targets:
        msmd.open('{0}{1}.split'.format(src_dir,target))
        spws = msmd.spwsforfield('{}'.format(target))
        msmd.close()
        for spw in spws:
            plot_file = plots_obs_dir+'{0}_amp_chn_spw{1}.png'.format(target,spw)
            logger.info('Plotting amplitude vs channel to {}'.format(plot_file))
            plotms(vis=src_dir+target+'.split.contsub', xaxis='chan', yaxis='amp',
                   ydatacolumn='corrected', spw=str(spw), plotfile=plot_file,
                   expformat='png', overwrite=True, showgui=False)
            plot_file = plots_obs_dir+'{0}_amp_vel_spw{1}.png'.format(target,spw)
            logger.info('Plotting amplitude vs velocity to {}'.format(plot_file))
            plotms(vis=src_dir+target+'.split.contsub', xaxis='velocity', yaxis='amp',
                   ydatacolumn='corrected', spw=str(spw), plotfile=plot_file,
                   expformat='png', overwrite=True, showgui=False,
                   freqframe='BARY', restfreq=str(config['global']['rest_freq']), veldef='OPTICAL')
    logger.info('Completed plotting amplitude spectrum.')

def dirty_cont_image(config,config_raw,config_file):
    """
    Generates a dirty image of each science target including the continuum emission.
    Checks that the pixel size and image size are set (will prompt user if in interactive mode).
    
    Input:
    config = The parameters read from the configuration file. (Ordered dictionary)
    config_raw = The instance of the parser.
    config_file = Path to configuration file. (String)
    """
    logger.info('Starting making dirty continuum image.')
    calib = config['calibration']
    rest_freq = config['global']['rest_freq']
    targets = calib['targets']
    cln_param = config['clean']
    src_dir = config['global']['src_dir']+'/'
    img_dir = config['global']['img_dir']+'/'
    makedir('/.'+img_dir)
    logger.info('Removing any existing dirty continuum images.')
    del_list = glob.glob(img_dir+'*cont.dirty*')
    for file_path in del_list:
        logger.info('Deleting: '+file_path)
        shutil.rmtree(file_path)
    logger.info('Checking clean parameters for dirty image (inc. continuum).')
    reset_cln = False
    if (len(cln_param['pix_size']) == 0) or (len(cln_param['pix_size']) != len(targets)):
        if not interactive:
            logger.critical('The number of pixel sizes provided does not match the number of targets.')
            logger.info('Pixel sizes: {}'.format(cln_param['pix_size']))
            logger.info('Targets: {}'.format(targets))
            sys.exit(-1)
        reset_cln = True
        if len(cln_param['pix_size']) < len(targets):
            logger.warning('There are more target fields than pixel sizes. Appending blanks.')
            while len(cln_param['pix_size']) < len(targets):
                cln_param['pix_size'].append('')
        elif len(cln_param['pix_size']) > len(targets):
            logger.warning('There are more pixel sizes than target fields.')
            logger.info('Current pixel sizes: {}'.format(cln_param['pix_size']))
            logger.warning('The pixel size list will now be truncated to match the number of targets.')
            cln_param['pix_size'] = cln_param['pix_size'][:len(targets)]
    elif interactive:
        print('Current pixel sizes set as:')
        for i in range(len(cln_param['pix_size'])):
            print(('{0}: {1}'.format(targets[i],cln_param['pix_size'][i])))
        resp = str(input('Do you want revise the pixel sizes (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln and interactive:
        print('For each target enter the desired pixel size:')
        for i in range(len(targets)):
            cln_param['pix_size'][i] = uinput('Pixel size for {}: '.format(targets[i]), cln_param['pix_size'][i])
            logger.info('Setting pixel size for {0} as: {1}.'.format(targets[i], cln_param['pix_size'][i]))
        logger.info('Updating config file to set pixel sizes.')
        config_raw.set('clean','pix_size',cln_param['pix_size'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    logger.info('Pixel sizes set as: {}.'.format(cln_param['pix_size']))
    logger.info('For the targets: {}.'.format(targets))
    reset_cln = False
    if len(cln_param['im_size']) == 0 or len(cln_param['im_size']) != len(targets):
        if not interactive:
            logger.critical('The number of image sizes provided does not match the number of targets.')
            logger.info('Image sizes: {}'.format(cln_param['im_size']))
            logger.info('Targets: {}'.format(targets))
            sys.exit(-1)
        reset_cln = True
        if len(cln_param['im_size']) < len(targets):
            logger.warning('There are more target fields than image sizes. Appending blanks.')
            while len(cln_param['im_size']) < len(targets):
                cln_param['im_size'].append('')
        elif len(cln_param['im_size']) > len(targets):
            logger.warning('There are more image sizes than target fields.')
            logger.info('Current image sizes: {} pixels.'.format(cln_param['im_size']))
            logger.warning('The image size list will now be truncated to match the number of targets.')
            cln_param['im_size'] = cln_param['im_size'][:len(targets)]
    elif interactive:
        print('Current images sizes set as:')
        for i in range(len(cln_param['im_size'])):
            print(('{0}: {1}'.format(targets[i],cln_param['im_size'][i])))
        resp = str(input('Do you want revise the image sizes (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln and interactive:
        print('For each target enter the desired image size:')
        for i in range(len(targets)):
            print(('Note: The pixel size for this target was set to: {}'.format(cln_param['pix_size'][i])))
            cln_param['im_size'][i] = uinput('Image size for {}: '.format(targets[i]), cln_param['im_size'][i])
            logger.info('Setting image size for {0} as: {1} x {2}.'.format(targets[i], cln_param['im_size'][i],cln_param['pix_size'][i]))
        logger.info('Updating config file to set image sizes.')
        config_raw.set('clean','im_size',cln_param['im_size'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    logger.info('Image sizes set as: {} pixels.'.format(cln_param['im_size']))
    logger.info('For the targets: {}.'.format(targets))
    for i in range(len(targets)):
        target = targets[i]
        logger.info('Making dirty image of {} (inc. continuum).'.format(target))
        command = "tclean(vis='{0}{1}'+'.split', field='{1}', imagename='{2}{1}'+'.cont.dirty', cell='{3}', imsize=[{4},{4}], specmode='cube', outframe='bary', veltype='radio', restfreq='{5}', gridder='wproject', wprojplanes=128, pblimit=0.1, normtype='flatnoise', deconvolver='hogbom', weighting='briggs', robust={6}, niter=0, interactive=False)".format(src_dir,target,img_dir,cln_param['pix_size'][i],cln_param['im_size'][i],rest_freq,cln_param['robust'])
        logger.info('Executing command: '+command)
        exec(command)  
    logger.info('Completed making dirty continuum image.')
            
def dirty_image(config,config_raw,config_file):
    """
    Generates a dirty (continuum subtracted) image of each science target.
    Checks that the pixel size, image size, and line emission channels are set (will prompt user if in interactive mode).
    
    Input:
    config = The parameters read from the configuration file. (Ordered dictionary)
    config_raw = The instance of the parser.
    config_file = Path to configuration file. (String)
    """
    logger.info('Starting making dirty image.')
    calib = config['calibration']
    contsub = config['continuum_subtraction']
    rest_freq = config['global']['rest_freq']
    targets = calib['targets']
    cln_param = config['clean']
    src_dir = config['global']['src_dir']+'/'
    img_dir = config['global']['img_dir']+'/'
    makedir('./'+img_dir)
    logger.info('Removing any existing dirty images.')
    for target in targets:
        del_list = glob.glob(img_dir+'{}.dirty*'.format(target))
        for file_path in del_list:
            logger.info('Deleting: '+file_path)
            shutil.rmtree(file_path)
    logger.info('Checking clean parameters for dirty image.')
    reset_cln = False
    if len(cln_param['pix_size']) == 0 or len(cln_param['pix_size']) != len(targets):
        if not interactive:
            logger.critical('The number of pixel sizes provided does not match the number of targets.')
            logger.info('Pixel sizes: {}'.format(cln_param['pix_size']))
            logger.info('Targets: {}'.format(targets))
            sys.exit(-1)
        reset_cln = True
        if len(cln_param['pix_size']) < len(targets):
            logger.warning('There are more target fields than pixel sizes. Appending blanks.')
            while len(cln_param['pix_size']) < len(targets):
                cln_param['pix_size'].append('')
        elif len(cln_param['pix_size']) > len(targets):
            logger.warning('There are more pixel sizes than target fields.')
            logger.info('Current pixel sizes: {}'.format(cln_param['pix_size']))
            logger.warning('The pixel size list will now be truncated to match the number of targets.')
            cln_param['pix_size'] = cln_param['pix_size'][:len(targets)]
    elif interactive:
        print('Current pixel sizes set as:')
        for i in range(len(cln_param['pix_size'])):
            print(('{0}: {1}'.format(targets[i],cln_param['pix_size'][i])))
        resp = str(input('Do you want revise the pixel sizes (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln and interactive:
        print('For each target enter the desired pixel size:')
        for i in range(len(targets)):
            cln_param['pix_size'][i] = uinput('Pixel size for {}: '.format(targets[i]), cln_param['pix_size'][i])
            logger.info('Setting pixel size for {0} as: {1}.'.format(targets[i], cln_param['pix_size'][i]))
        logger.info('Updating config file to set pixel sizes.')
        config_raw.set('clean','pix_size',cln_param['pix_size'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    logger.info('Pixel sizes set as: {}.'.format(cln_param['pix_size']))
    logger.info('For the targets: {}.'.format(targets))
    reset_cln = False
    if len(cln_param['im_size']) == 0 or len(cln_param['im_size']) != len(targets):
        if not interactive:
            logger.critical('The number of image sizes provided does not match the number of targets.')
            logger.info('Image sizes: {}'.format(cln_param['im_size']))
            logger.info('Targets: {}'.format(targets))
            sys.exit(-1)
        reset_cln = True
        if len(cln_param['im_size']) < len(targets):
            logger.warning('There are more target fields than image sizes. Appending blanks.')
            while len(cln_param['im_size']) < len(targets):
                cln_param['im_size'].append('')
        elif len(cln_param['im_size']) > len(targets):
            logger.warning('There are more image sizes than target fields.')
            logger.info('Current image sizes: {} pixels.'.format(cln_param['im_size']))
            logger.warning('The image size list will now be truncated to match the number of targets.')
            cln_param['im_size'] = cln_param['im_size'][:len(targets)]
    elif interactive:
        print('Current images sizes set as:')
        for i in range(len(cln_param['im_size'])):
            print(('{0}: {1}'.format(targets[i],cln_param['im_size'][i])))
        resp = str(input('Do you want revise the image sizes (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln and interactive:
        print('For each target enter the desired image size:')
        for i in range(len(targets)):
            print(('Note: The pixel size for this target was set to: {}'.format(cln_param['pix_size'][i])))
            cln_param['im_size'][i] = uinput('Image size for {}: '.format(targets[i]), cln_param['im_size'][i])
            logger.info('Setting image size for {0} as: {1} x {2}.'.format(targets[i], cln_param['im_size'][i],cln_param['pix_size'][i]))
        logger.info('Updating config file to set image sizes.')
        config_raw.set('clean','im_size',cln_param['im_size'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    logger.info('Image sizes set as: {} pixels.'.format(cln_param['im_size']))
    logger.info('For the targets: {}.'.format(targets))
    reset_cln = False
    if len(cln_param['line_ch']) == 0 or len(cln_param['line_ch']) != len(targets):
        if not interactive:
            logger.critical('The number of line channel ranges provided does not match the number of targets.')
            logger.info('Pixel sizes: {}'.format(cln_param['line_ch']))
            logger.info('Targets: {}'.format(targets))
            sys.exit(-1)
        reset_cln = True
        if len(cln_param['line_ch']) < len(targets):
            logger.warning('There are more target fields than channel ranges. Appending blank ranges.')
            while len(cln_param['line_ch']) < len(targets):
                cln_param['line_ch'].append('')
        elif len(cln_param['line_ch']) > len(targets):
            logger.warning('There are more channel ranges than target fields.')
            logger.info('Current channel ranges: {}'.format(cln_param['line_ch']))
            logger.warning('The channel range list will now be truncated to match the number of targets.')
            cln_param['line_ch'] = cln_param['line_ch'][:len(targets)]
    elif interactive:
        print('Current image channels set as:')
        for i in range(len(cln_param['line_ch'])):
            print(('{0}: {1}'.format(targets[i],cln_param['line_ch'][i])))
        resp = str(input('Do you want revise the channels that will be imaged (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln and interactive:
        print('For each target enter the channels you want to image in the following format:\nspwID:min_ch~max_ch')
        for i in range(len(targets)):
            print(('Note: The continuum channels for this target were set to: {}'.format(contsub['linefree_ch'][i])))
            cln_param['line_ch'][i] = uinput('Channels to image for {}: '.format(targets[i]), cln_param['line_ch'][i])
            logger.info('Setting image channels for {0} as: {1}.'.format(targets[i], cln_param['line_ch'][i]))
        logger.info('Updating config file to set channels to be imaged.')
        config_raw.set('clean','line_ch',cln_param['line_ch'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    logger.info('Line emission channels set as: {}.'.format(cln_param['line_ch']))
    logger.info('For the targets: {}.'.format(targets))
    for i in range(len(targets)):
        target = targets[i]
        logger.info('Making dirty image of {} (line only).'.format(target))
        command = "tclean(vis='{0}{1}'+'.split.contsub', field='{1}', imagename='{2}{1}'+'.dirty', cell='{3}', imsize=[{4},{4}], specmode='cube', outframe='bary', veltype='radio', restfreq='{5}', gridder='wproject', wprojplanes=128, pblimit=0.1, normtype='flatnoise', deconvolver='hogbom', weighting='briggs', robust={6}, restoringbeam='common', niter=0, interactive=False)".format(src_dir,target,img_dir,cln_param['pix_size'][i],cln_param['im_size'][i],rest_freq,cln_param['robust'])
        logger.info('Executing command: '+command)
        exec(command)
    logger.info('Completed making dirty image.')
        
def noise_est(config):
    """
    Makes an estimate of the theortically expected noise level for each science target.
    
    Input:
    config = The parameters read from the configuration file. (Ordered dictionary)
    
    Output:
    noise = Estimate of the theortical noise in Jy/beam. (List of Floats)
    """
    logger.info('Starting making noise estimation.')
    targets = config['calibration']['targets']
    cln_param = config['clean']
    src_dir = config['global']['src_dir']+'/'
    noise = []
    for target in targets:
        msmd.open(src_dir+target+'.split.contsub')
        N = msmd.nantennas()
        t_int = msmd.effexposuretime()['value']
        ch_wid = numpy.mean(msmd.chanwidths(0))
        #Note: The above line may cause issues if different spectral windows
        #have very difference frequency resolutions
        msmd.close()
        corr_eff = cln_param['corr_eff']
        SEFD = cln_param['sefd']
        N_pol = 2.
        noise.append(SEFD/(corr_eff*numpy.sqrt(N_pol*N*(N-1.)*t_int*ch_wid)))
    logger.info('Completed making noise estimation.')
    return noise

def image(config,config_raw,config_file):
    """
    Generates a clean (continuum subtracted) image of each science target.
    Checks that the CLEANing scales and line emission channels are set (may prompt user if in interactive mode).
    Makes varies check on the ratio of pixel size to beam size and the scales and the maximum baseline (may prompt user if in interactive mode).
    Exports the final images as fits cubes (after regridding to J2000 if necessary).
    
    Input:
    config = The parameters read from the configuration file. (Ordered dictionary)
    config_raw = The instance of the parser.
    config_file = Path to configuration file. (String)
    """
    noises = noise_est(config)
    calib = config['calibration']
    contsub = config['continuum_subtraction']
    rest_freq = config['global']['rest_freq']
    targets = calib['targets']
    cln_param = config['clean']
    src_dir = config['global']['src_dir']+'/'
    img_dir = config['global']['img_dir']+'/'
    makedir('./'+img_dir)
    logger.info('Removing any existing images.')
    for target in targets:
        del_list = glob.glob(img_dir+'{}.image'.format(target))
        for file_path in del_list:
            logger.info('Deleting: '+file_path)
            shutil.rmtree(file_path)
        del_list = glob.glob(img_dir+'{}.model'.format(target))
        for file_path in del_list:
            logger.info('Deleting: '+file_path)
            shutil.rmtree(file_path)
        del_list = glob.glob(img_dir+'{}.pb'.format(target))
        for file_path in del_list:
            logger.info('Deleting: '+file_path)
            shutil.rmtree(file_path)
        del_list = glob.glob(img_dir+'{}.psf'.format(target))
        for file_path in del_list:
            logger.info('Deleting: '+file_path)
            shutil.rmtree(file_path)
        del_list = glob.glob(img_dir+'{}.residual'.format(target))
        for file_path in del_list:
            logger.info('Deleting: '+file_path)
            shutil.rmtree(file_path)
        del_list = glob.glob(img_dir+'{}.sumwt'.format(target))
        for file_path in del_list:
            logger.info('Deleting: '+file_path)
            shutil.rmtree(file_path)
    logger.info('Starting generation of clean image(s).')
    reset_cln = False
    reset_cln = False
    if len(cln_param['line_ch']) == 0 or len(cln_param['line_ch']) != len(targets):
        if not interactive:
            logger.critical('The number of line channel ranges provided does not match the number of targets.')
            logger.info('Pixel sizes: {}'.format(cln_param['line_ch']))
            logger.info('Targets: {}'.format(targets))
            sys.exit(-1)
        reset_cln = True
        if len(cln_param['line_ch']) < len(targets):
            logger.warning('There are more target fields than channel ranges. Appending blank ranges.')
            while len(cln_param['line_ch']) < len(targets):
                cln_param['line_ch'].append('')
        elif len(cln_param['line_ch']) > len(targets):
            logger.warning('There are more channel ranges than target fields.')
            logger.info('Current channel ranges: {}'.format(cln_param['line_ch']))
            logger.warning('The channel range list will now be truncated to match the number of targets.')
            cln_param['line_ch'] = cln_param['line_ch'][:len(targets)]
    elif interactive:
        print('Current image channels set as:')
        for i in range(len(cln_param['line_ch'])):
            print(('{0}: {1}'.format(targets[i],cln_param['line_ch'][i])))
        resp = str(input('Do you want revise the channels that will be imaged (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln and interactive:
        print('For each target enter the channels you want to image in the following format:\nspwID:min_ch~max_ch')
        for i in range(len(targets)):
            print(('Note: The continuum channels for this target were set to: {}'.format(contsub['linefree_ch'][i])))
            cln_param['line_ch'][i] = uinput('Channels to image for {}: '.format(targets[i]), cln_param['line_ch'][i])
            logger.info('Setting image channels for {0} as: {1}.'.format(targets[i], cln_param['line_ch'][i]))
        logger.info('Updating config file to set channels to be imaged.')
        config_raw.set('clean','line_ch',cln_param['line_ch'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    logger.info('Line emission channels set as: {}.'.format(cln_param['line_ch']))
    logger.info('For the targets: {}.'.format(targets))
    if cln_param['multiscale']:
        algorithm = 'multiscale'
        logger.info('Setting CLEAN algorithm to MS-CLEAN.')
        reset_cln = False
        if cln_param['scales'] == []:
            reset_cln = True
            logger.warning('MS-CLEAN scales not set.')
        elif 0 not in cln_param['scales']:
            logger.warning('MS-CLEAN scales do not include point sources. This is highly recommended.')
            if interactive:
                resp = str(input('Do you want revise MS-CLEAN scales (y/n): '))
                if resp.lower() in ['yes','ye','y']:
                    reset_cln = True
            else:
                logger.info('Adding point source to MS-CLEAN scales.')
                cln_param['scales'].append(0)
                reset_cln = True
        if reset_cln:
            if interactive:
                print(('Current scales set to: {} beam diameters.'.format(cln_param['scales'])))
                cln_param['scales'] = uinput('Enter new scales: ', cln_param['scales'])
            logger.info('Setting MS-CLEAN scales as {} beams.'.format(cln_param['scales']))
            logger.info('Updating config file to set MS-CLEAN scales.')
            config_raw.set('clean','scales',cln_param['scales'])
            configfile = open(config_file,'w')
            config_raw.write(configfile)
            configfile.close()
            reset_cln = False
        scales = cln_param['scales']
    else:
        algorithm = 'hogbom'
        logger.info('Setting CLEAN algorithm to Hogbom.')
        scales = None
    for i in range(len(targets)):
        target = targets[i]
        logger.info('Starting {} image.'.format(target))
        reset_cln = False
        ia.open(img_dir+target+'.dirty.image')
        rest_beam = ia.restoringbeam()
        ia.close()
        if rest_beam['minor']['unit'] not in cln_param['pix_size'][i]:
            logger.error('The pixel size and beam size have diffent units.')
            if cln_param['multiscale']:
                logger.error('MS-CLEAN scales will likely be incorrect.')
            logger.info('Pixel size: {}'.format(cln_param['pix_size'][i]))
            logger.info('Beam size units: {}'.format(rest_beam['minor']['unit']))
        pix_size = cln_param['pix_size'][i]
        pix_size = float(pix_size[:pix_size.find(rest_beam['minor']['unit'])])
        if pix_size > 0.2*rest_beam['minor']['value']:
            logger.warning('There are fewer than 5 pixels across the beam minor axis. Consider decreasing the pixel size.')
            if interactive:
                print('Beam dimensions:')
                print(('Major: {0:.2f} {1}'.format(rest_beam['major']['value'],rest_beam['major']['unit'])))
                print(('Minor: {0:.2f} {1}'.format(rest_beam['minor']['value'],rest_beam['minor']['unit'])))
                print(('Pixel size: {}'.format(cln_param['pix_size'])))
                resp = str(input('Do you want revise the pixel size (y/n): '))
                if resp.lower() in ['yes','ye','y']:
                    reset_cln = True
        if reset_cln and interactive:
            print('Enter the desired pixel size:')
            cln_param['pix_size'][i] = uinput('Pixel size for {}: '.format(target), cln_param['pix_size'][i])
            logger.info('Setting pixel size for {0} as: {1}.'.format(target, cln_param['pix_size'][i]))
            logger.info('Updating config file to set pixel size.')
            config_raw.set('clean','pix_size',cln_param['pix_size'])
            configfile = open(config_file,'w')
            config_raw.write(configfile)
            configfile.close()
            reset_cln = False
        if cln_param['automask_sl'] == '':
            cln_param['automask_sl'] == 2.0
            logger.warning('Automasking sidelobe threshold not set. Using default value: {}'.format(cln_param['automask_sl']))
        if cln_param['automask_ns'] == '':
            cln_param['automask_ns'] == 4.25
            logger.warning('Automasking noise threshold not set. Using default value: {}'.format(cln_param['automask_ns']))
        if cln_param['automask_lns'] == '':
            cln_param['automask_lns'] == 1.5
            logger.warning('Automasking low noise threshold not set. Using default value: {}'.format(cln_param['automask_lns']))
        if cln_param['automask_mbf'] == '':
            cln_param['automask_mbf'] == 0.3
            logger.warning('Automasking minimum beam fraction not set. Using default value: {}'.format(cln_param['automask_mbf']))
        if cln_param['automask_neg'] == '':
            cln_param['automask_neg'] == 15.0
            logger.warning('Automasking negative threshold not set. Using default value: {}'.format(cln_param['automask_neg']))
        logger.info('Automasking parameters set as:')
        logger.info('sidelobethreshold = {}'.format(cln_param['automask_sl']))
        logger.info('noisethreshold = {}'.format(cln_param['automask_ns']))
        logger.info('lownoisethreshold = {}'.format(cln_param['automask_lns']))
        logger.info('minbeamfraction = {}'.format(cln_param['automask_mbf']))
        logger.info('negativethreshold = {}'.format(cln_param['automask_neg']))
        if cln_param['multiscale']:
            pix_size = cln_param['pix_size'][i]
            pix_size = float(pix_size[:pix_size.find(rest_beam['minor']['unit'])])
            pix_per_beam = rest_beam['major']['value']/pix_size
            scales = cln_param['scales']
            scales = list(numpy.array(numpy.array(scales)*pix_per_beam,dtype='int'))
            B_min = au.getBaselineLengths('{0}{1}'+'.split.contsub'.format(src_dir,target), sort=True)[0][1]
            msmd.open('{0}{1}'+'.split.contsub'.format(src_dir,target))
            spws = msmd.spwsforfield(target)
            f_min = None
            for spw in spws:
                if f_min == None or f_min > min(msmd.chanfreqs(spw=spw,unit='Hz')):
                    f_min = min(msmd.chanfreqs(spw=spw,unit='Hz'))
            msmd.close()
            max_scale = 180.*3600.*299792458./(1.2*numpy.pi*f_min*b_min)
            logger.info('The maximum recoverable scale for {0} is {1} arcsec.'.format(target,int(max_scale)))
            if 'arcsec' not in cln_param['pix_size'][i]:
                logger.warning('Pixel size not in arcsec. Maximum scale not checked.')
            else:
                pix_size = cln_param['pix_size'][i]
                pix_size = float(pix_size[:pix_size.find('arcsec')])
                if max(scales)*pix_size > max_scale:
                    logger.warning('Some MS-CLEAN scale(s) is (are) larger than largest recoverable angular scales.')
                    logger.info('Removing offending scales.')
                    scales = list(set(numpy.where(numpy.array(scales)*pix_size <= max_scale,scales,0)))
            logger.info('CLEANing with scales of {} pixels.'.format(scales))
        logger.info('CLEANing {0} to a threshold of {1} Jy.'.format(target,noises[i]*cln_param['thresh']))
        command = "tclean(vis='{0}{1}'+'.split.contsub', field='{1}', spw='{2}', imagename='{3}{1}', cell='{4}', imsize=[{5},{5}], specmode='cube', outframe='bary', veltype='radio', restfreq='{6}', gridder='wproject', wprojplanes=128, pblimit=0.1, normtype='flatnoise', deconvolver='{7}', scales={8}, restoringbeam='common', pbcor=True, weighting='briggs', robust={9}, niter=100000, gain=0.1, threshold='{10}Jy', usemask='auto-multithresh', sidelobethreshold={11}, noisethreshold={12}, lownoisethreshold={13}, minbeamfrac={14}, negativethreshold={15}, cyclefactor=2.0,interactive=False)".format(src_dir,target,cln_param['line_ch'][i],img_dir,cln_param['pix_size'][i],cln_param['im_size'][i],rest_freq,algorithm,scales,cln_param['robust'],noises[i]*cln_param['thresh'],cln_param['automask_sl'],cln_param['automask_ns'],cln_param['automask_lns'],cln_param['automask_mbf'],cln_param['automask_neg'])
        logger.info('Executing command: '+command)
        exec(command)
        logger.info('CLEANing finished. Image cube saved as {}.'.format(target+'.image'))
        ia.open(img_dir+target+'.dirty.image')
        coords = ia.coordsys()
        if 'J2000' not in coords.referencecode()[0]:
            coord_chn = True
            logger.info('Coordinate system not J2000. Image will be regridded.')
            command = "imregrid(imagename='{0}{1}'+'.image', template='J2000', output='{0}{1}'+'.image.J2000', asvelocity=True, interpolation='linear', decimate=10, overwrite=True)".format(img_dir,target)
            logger.info('Executing command: '+command)
            exec(command)
            logger.info('{} regridded in J2000 coordinates.'.format(target+'.image.J2000'))
            command = "imregrid(imagename='{0}{1}'+'.image.pbcor', template='J2000', output='{0}{1}'+'.image.pbcor.J2000', asvelocity=True, interpolation='linear', decimate=10, overwrite=True)".format(img_dir,target)
            logger.info('Executing command: '+command)
            exec(command)
            logger.info('{} regridded in J2000 coordinates.'.format(target+'.image.pbcor.J2000'))
        coords.done()
        ia.close()
        fitsname = target+'_HI.fits'
        logger.info('Saving image cube as {}'.format(fitsname))
        if coord_chn:
            imagename = target+'.image.J2000'
        else:
            imagename = target+'.image'
        command = "exportfits(imagename='{0}{1}', fitsimage='{0}{2}', velocity=True,optical=False,overwrite=True,dropstokes=True,stokeslast=True,history=True,dropdeg=True)".format(img_dir,imagename,fitsname)
        logger.info('Executing command: '+command)
        exec(command)
        fitsname = target+'_HI.pbcor.fits'
        logger.info('Saving primary beam corrected image cube as {}'.format(fitsname))
        if coord_chn:
            imagename = target+'.image.pbcor.J2000'
        else:
            imagename = target+'.image.pbcor'
        command = "exportfits(imagename='{0}{1}', fitsimage='{0}{2}', velocity=True,optical=False,overwrite=True,dropstokes=True,stokeslast=True,history=True,dropdeg=True)".format(img_dir,imagename,fitsname)
        logger.info('Executing command: '+command)
        exec(command)
        coord_chn = False
    logger.info('Completed generation of clean image(s).')
    
    
def cleanup(config):
    """
    Deleted non-essential files at the end of the pipeline.
    Uses the 'cleanup_level' parameter. The levels are as follows:
    1) Calibration and flagging tabled deleted as well as CASA .last files.
    2) In addition to 1, the full (not split) MS is deleted along with the dirty images amd non-essential output from tclean.
    3) Everything except the final fits cubes and the summary information is deleted.
    
    Input:
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    src_dir = config['global']['src_dir']+'/'
    img_dir = config['global']['img_dir']+'/'
    cln_lvl = config['global']['cleanup_level']
    logger.info('Starting level {} cleanup.'.format(cln_lvl))
    if cln_lvl >= 1:
        logger.info('Deleting CASA .last files.')
        del_list = glob.glob('./*.last')
        for file_path in del_list:
            os.remove(file_path)
        logger.info('Deleting calibration tables.')
        shutil.rmtree('./cal_tabs')
        logger.info('Deleting flag tables.')
        shutil.rmtree('./{}.flagversions'.format(msfile))
    if cln_lvl >= 2:
        logger.info('Deleting full measurement set.')
        shutil.rmtree('./{}'.format(msfile))        
        logger.info('Deleting dirty images.')
        del_list = glob.glob(img_dir+'*.dirty.*')
        for file_path in del_list:
            shutil.rmtree(file_path)
        logger.info('Deleting CLEANing masks.')
        del_list = glob.glob(img_dir+'*.mask')
        for file_path in del_list:
            shutil.rmtree(file_path)
        logger.info('Deleting CLEAN models.')
        del_list = glob.glob(img_dir+'*.model')
        for file_path in del_list:
            shutil.rmtree(file_path)
        logger.info('Deleting primary beam and PSF models.')
        del_list = glob.glob(img_dir+'*.pb')
        for file_path in del_list:
            shutil.rmtree(file_path)
        del_list = glob.glob(img_dir+'*.psf')
        for file_path in del_list:
            shutil.rmtree(file_path)
        logger.info('Deleting weighting.')
        del_list = glob.glob(img_dir+'*.sumwt')
        for file_path in del_list:
            shutil.rmtree(file_path)
    if cln_lvl >= 3:
        logger.info('Deleting split measurement sets.')
        shutil.rmtree(src_dir)
        logger.info('Deleting CLEAN residuals.')
        del_list = glob.glob(img_dir+'*.residual')
        for file_path in del_list:
            shutil.rmtree(file_path)
        logger.info('Deleting image files (except fits).')
        del_list = glob.glob(img_dir+'*.image*')
        for file_path in del_list:
            shutil.rmtree(file_path)
    logger.info('Cleanup completed.')

######################   Processing   ####################
# Read configuration file with parameters
config_file = sys.argv[-1]
config,config_raw = read_config(config_file)
interactive = config['global']['interactive']

# Set up your logger
logger = get_logger(LOG_FILE_INFO  = '{}_log.log'.format(config['global']['project_name']),
                    LOG_FILE_ERROR = '{}_errors.log'.format(config['global']['project_name'])) # Set up your logger

# Start processing
msfile = '{0}.ms'.format(config['global']['project_name'])

# 1. Import data and write listobs to file
data_path = config['importdata']['data_path']
data_files = glob.glob(os.path.join(data_path, '*'))
import_data(sorted(data_files), msfile)
msinfo = get_msinfo(msfile)

# 2. Diagnostic plots
plot_elevation(msfile,config)
plot_ants(msfile)

# 3. Apply baisc flags
base_flags(msfile,config)
tfcrop(msfile)
manual_flags()
flag_version = 'initial'
rmdir('{0}.flagversions/flags.{1}'.format(msfile,flag_version))
flag_sum(msfile,flag_version)
save_flags(msfile,flag_version)

# 4. Calibration
restore_flags(msfile,'initial')
select_refant(msfile,config,config_raw,config_file)
set_fields(msfile,config,config_raw,config_file)
calibration(msfile,config)
rflag(msfile,config)
flag_version = 'rflag'
flag_sum(msfile,flag_version)
rmdir('{0}.flagversions/flags.{1}'.format(msfile,flag_version))
save_flags(msfile,flag_version)
extend_flags(msfile)
flag_version = 'extended'
flag_sum(msfile,flag_version)
rmdir('{0}.flagversions/flags.{1}'.format(msfile,flag_version))
save_flags(msfile,flag_version)
calibration(msfile,config)
flag_version = 'final'
flag_sum(msfile,flag_version)
rmdir('{0}.flagversions/flags.{1}'.format(msfile,flag_version))
save_flags(msfile,flag_version)

#5. Split, continuum subtract and make dirty image
restore_flags(msfile,'final')
rmdir(config['global']['src_dir'])
split_fields(msfile,config)
dirty_cont_image(config,config_raw,config_file)
contsub(msfile,config,config_raw,config_file)
plot_spec(config)
dirty_image(config,config_raw,config_file)

#6. Clean and regrid (if necessary) image
image(config,config_raw,config_file)

#7. Cleanup
cleanup(config)
