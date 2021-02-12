import imp, os, glob, collections
imp.load_source('common_functions','common_functions.py')
import common_functions as cf


def import_data(data_files, msfile, config, config_raw, logger):
    """ 
    Import VLA archive files from a location to a single MS.
    
    Input:
    data_files = Paths to the VLA archive files. (List/Array of Strings)
    msfile = Path where the MS will be created. (String)
    """
    logger.info('Starting import vla data')
    sum_dir = './summary/'
    cf.makedir(sum_dir,logger)
    cf.rmdir(msfile,logger)
    logger.info('Input files: {}'.format(data_files))
    logger.info('Output msfile: {}'.format(msfile))
    command = "importvla(archivefiles = {0}, vis = '{1}')".format(data_files, msfile)
    logger.info('Executing command: '+command)
    exec(command)
    cf.check_casalog(config,config_raw,logger,casalog)
    logger.info('Completed import vla data')
    
def obs_dates(msfile, config, logger):
    """
    Reads the observation date and time for each file imported and prints to log.
    
    Input:
    msfile = Path where the MS will be created. (String)
    """
    logger.info('Starting archive file summary.')
    logger.info('To find the exact files imported here search the VLA archive (https://archive.nrao.edu/archive/advquery.jsp) for:')
    tb.open(msfile+'/OBSERVATION')
    times = tb.getcol('TIME_RANGE')
    tb.close()
    for i in range(len(times[0])):
        start_time = qa.time({'value':times[0][i],'unit':'s'},form='fits')[0]
        end_time = qa.time({'value':times[1][i],'unit':'s'},form='fits')[0]
        start_time = start_time.replace('T',' ')
        end_time = end_time.replace('T',' ')
        logger.info('Project: {0}\tStart Time: {1}\tEnd Time: {2}'.format(config['global']['project_name'],start_time,end_time))
    logger.info('Completed archive file summary.')
    
def listobs_sum(msfile, config, config_raw, logger):
    """ 
    Write the listobs summary to file.
    
    Input:
    msfile = Path where the MS will be created. (String)
    """
    logger.info('Starting listobs summary.')
    sum_dir = './summary/'
    cf.makedir(sum_dir,logger)
    listobs_file = sum_dir+msfile+'.listobs.summary'
    cf.rmfile(listobs_file,logger)
    logger.info('Writing listobs summary of data set to: {}'.format(listobs_file))
    listobs(vis=msfile, listfile=listobs_file)
    cf.check_casalog(config,config_raw,logger,casalog)
    logger.info('Completed listobs summary.')

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

def find_mssources(msfile,logger):
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

def get_msinfo(msfile,logger):
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
    msinfo['mssources'] = find_mssources(msfile,logger)
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
def plot_elevation(msfile,config,logger):
    """
    Plots the elevation of the fields in each SPW as a function of time.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    """
    logger.info('Starting plotting elevation.')
    plots_obs_dir = './plots/'
    cf.makedir(plots_obs_dir,logger)
    plot_file = plots_obs_dir+'{0}_elevation.png'.format(msfile)
    logger.info('Plotting elevation to: {}'.format(plot_file))
    avgtime = 16
    width = 900
    min_elev = 0
    max_elev = 90
    showgui = False
    plotms(vis=msfile, xaxis='time', yaxis='elevation',
            correlation='', coloraxis = 'field',
            symbolsize=5, plotrange=[-1,-1, min_elev, max_elev],  
            averagedata=True, avgtime=str(avgtime), plotfile = plot_file,
            expformat = 'png', customsymbol = True, symbolshape = 'circle',
            overwrite=True, showlegend=False, showgui=showgui,
            exprange='all', iteraxis='spw')
    logger.info('Completed plotting elevation.')

def plot_ants(msfile,logger):
    """
    Plots the layout of the antennae during the observations
    
    Input:
    msfile = Path to the MS. (String)
    """
    logger.info('Starting plotting antenna positions.')
    plots_obs_dir = './plots/'
    cf.makedir(plots_obs_dir,logger)
    plot_file = plots_obs_dir+'{0}_antpos.png'.format(msfile)
    logger.info('Plotting antenna positions to: {}'.format(plot_file))
    plotants(vis=msfile,figfile=plot_file)
    logger.info('Completed plotting antenna positions.')
    
def transform_data(msfile,config,config_raw,config_file,logger):
    """
    Allows the user to alter the data set by selection only specific observations, fields, and SPWs.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    config_raw = The instance of the parser.
    config_file = Path to configuration file. (String)
    """
    logger.info('Starting data transform.')
    importdata = config['importdata']
    chanavg = False
    if not importdata['mstransform']:
        if interactive:
            print('You may want to review the listobs summary of the imported data to decide if certain observations, SPWs, or fields should be removed.')
            resp = ''
            while (resp.lower() not in ['yes','ye','y']) and (resp.lower() not in ['no','n']) :
                resp = str(raw_input('Do you want to transform the data set (y/n): '))
            if resp.lower() in ['yes','ye','y']:
                importdata['mstransform'] = True
    if importdata['mstransform']:
        if interactive:
            print('Select which observations, SPWs, and fields to keep in the MS.')
            print('Blank strings mean all.')
            importdata['keep_obs'] = [cf.uinput('The following observations will be kept: ', importdata['keep_obs'])]
            importdata['keep_spws'] = [cf.uinput('The following SPWs will be kept: ', importdata['keep_spws'])]
            importdata['keep_fields'] = [cf.uinput('The following fields will be kept: ', importdata['keep_fields'])]
            resp = ''
            while (resp.lower() not in ['yes','ye','y']) and (resp.lower() not in ['no','n']) :
                resp = str(raw_input('Do you want to perform channel averaging (y/n): '))
            if resp.lower() in ['yes','ye','y']:
                chanavg = True
                importdata['chanavg'] = int(cf.uinput('Enter the number of channels to be averaged together: ', importdata['chanavg']))
        command = "mstransform(vis='{0}', outputvis='{0}_1', field='{1}', spw='{2}', observation='{3}', datacolumn='data'".format(msfile,','.join(importdata['keep_fields']),','.join(importdata['keep_spws']),','.join(importdata['keep_obs']))
        if config_raw.has_option('importdata','hanning'):
            if config['importdata']['hanning']:
                command += ', hanning=True'
        if config_raw.has_option('importdata','chanavg') or chanavg:
            if importdata['chanavg'] > 1:
                command += ', chanaverage=True, chanbin='+str(importdata['chanavg'])
        command += ')'
        logger.info('Executing command: '+command)
        exec(command)           
        cf.check_casalog(config,config_raw,logger,casalog)
        logger.info('Updating config file ({0}) to set mstransform values.'.format(config_file))
        config_raw.set('importdata','keep_obs',importdata['keep_obs'])
        config_raw.set('importdata','keep_spws',importdata['keep_spws'])
        config_raw.set('importdata','keep_fields',importdata['keep_fields'])
        if config_raw.has_option('importdata','chanavg') or chanavg:
            config_raw.set('importdata','chanavg',importdata['chanavg'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
        cf.rmdir(msfile+'.flagversions',logger)
        cf.makedir(msfile+'.flagversions',logger)
        cf.rmdir(msfile,logger)
        cf.mvdir(msfile+'_1',msfile,logger)
        logger.info('Completed data transformation.')
        listobs_sum(msfile,config,config_raw,logger)
    else:
        logger.info('No transformation made.')
        
def hanning_smooth(msfile,config,config_raw,config_file,logger):
    """
    Hanning smooths the dataset and replaces the previous version.
    
    Input:
    msfile = Path to the MS. (String)
    config = The parameters read from the configuration file. (Ordered dictionary)
    config_raw = The instance of the parser.
    config_file = Path to configuration file. (String)
    """
    logger.info('Starting Hanning smoothing.')
    importdata = config['importdata']
    command = "hanningsmooth(vis='{0}', outputvis='{0}_1')".format(msfile)
    logger.info('Executing command: '+command)
    exec(command)           
    cf.check_casalog(config,config_raw,logger,casalog)
    cf.rmdir(msfile+'.flagversions',logger)
    cf.makedir(msfile+'.flagversions',logger)
    cf.rmdir(msfile,logger)
    cf.mvdir(msfile+'_1',msfile,logger)
    logger.info('Completed Hanning smoothing.')

# Read configuration file with parameters
config_file = sys.argv[-1]
config,config_raw = cf.read_config(config_file)
interactive = config['global']['interactive']

# Set up your logger
logger = cf.get_logger(LOG_FILE_INFO  = '{}.log'.format(config['global']['project_name']),
                    LOG_FILE_ERROR = '{}_errors.log'.format(config['global']['project_name']),
                    new_log = True) # Set up your logger

# Define MS file name
msfile = '{0}.ms'.format(config['global']['project_name'])

# Import data, write listobs to file, and plot positions and elevation
cf.check_casaversion(logger)
cf.rmdir('summary',logger)
cf.rmdir('plots',logger)
cf.rmdir(msfile,logger)
cf.rmdir(msfile+'.flagversions',logger)
data_path = config['importdata']['data_path']
if not config['importdata']['jvla']:
    data_files = glob.glob(os.path.join(data_path, '*'))
    import_data(sorted(data_files), msfile, config, config_raw, logger)
    obs_dates(msfile, config, logger)
else:
    os.symlink(data_path+msfile,msfile)
    os.symlink(data_path+msfile+'.flagversions',msfile+'.flagversions')
listobs_sum(msfile,config,config_raw,logger)
transform_data(msfile,config,config_raw,config_file,logger)
if config_raw.has_option('importdata','hanning') and not config['importdata']['mstransform']:
    if config['importdata']['hanning']:
        hanning_smooth(msfile,config,config_raw,config_file,logger)
msinfo = get_msinfo(msfile,logger)
plot_elevation(msfile,config,logger)
plot_ants(msfile,logger)

#Review and backup parameters file
cf.diff_pipeline_params(config_file,logger)
cf.backup_pipeline_params(config_file,logger)
