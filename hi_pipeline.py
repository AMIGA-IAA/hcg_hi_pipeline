import time
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
    if not os.path.isfile(configfile):
        logger.critical('configfile: {} not found'.format(configfile))
        sys.exit()
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
def makedir(pathdir):
    try:
        os.mkdir(pathdir)
        logger.info('Create directory: {}'.format(pathdir))
    except:
        logger.debug('Cannot create directory: {}'.format(pathdir))
        pass

def rmdir(pathdir,message='Deleted:'):
    if os.path.exists(pathdir):
        try:
            shutil.rmtree(pathdir)
            logger.info('{0} {1}'.format(message, pathdir))
        except:
            logger.debug('Could not delete: {0} {1}'.format(message, pathdir))
            pass


def rmfile(pathdir,message='Deleted:'):
    if os.path.exists(pathdir):
        try:
            os.remove(pathdir)
            logger.info('{0} {1}'.format(message, pathdir))
        except:
            logger.debug('Could not delete: {0} {1}'.format(message, pathdir))
            pass
        
#User input function
def uinput(prompt, default=''):
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
    file_handler_info = logging.FileHandler(LOG_FILE_INFO, mode='w')
    file_handler_info.setFormatter(log_formatter)
    file_handler_info.setLevel(logging.INFO)
    logger.addHandler(file_handler_info)
    
    logger.setLevel(logging.INFO)
    return logger


def import_data(data_files, msfile):
    """ Import VLA archive files from a location to a single MS """
    logger.info('Starting import vla data')
    listobs_file = msfile+'.listobs.txt'
    rmdir(msfile)
    rmfile(listobs_file)
    logger.info('Input files: {}'.format(data_files))
    logger.info('Output msfile: {}'.format(msfile))
    importvla(archivefiles = data_files, vis = msfile)
    listobs(vis=msfile, listfile=listobs_file)
    logger.info('Finished import vla data')


def get_obsfreq(msfile):
    """ Returns freq of first and last channels, channel resolution
     and number of channels (first spw) in GHz """
    msmd.open(msfile)
    nspw = msmd.nspw()
    freq_ini = msmd.chanfreqs(0)[0]/1e9
    freq_end = msmd.chanfreqs(nspw-1)[-1]/1e9
    chan_res = msmd.chanwidths(0)[0]/1e9
    nchan = len(msmd.chanwidths(0))
    msmd.done()
    return freq_ini, freq_end, chan_res, nchan

def find_mssources(msfile):
    """ Extract source names from msfile metadata.
    Output format is a comma-separated string """
    msmd.open(msfile)
    mssources = ','.join(np.sort(msmd.fieldnames()))
    msmd.done()
    logger.debug('Sources in MS {0}: {1}'.format(msfile, mssources))
    return mssources

def get_project(msfile):
    """ Extract project code from msfile metadata """
    tb.open(msfile+'/OBSERVATION')
    project = tb.getcol('PROJECT')
    tb.close()
    return project[0]

def get_msinfo(msfile):
    """ Extracts and prints basic information from the measurement set"""
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
def plot_elevation(config):
    """ Plots the elevation of the target fields as a function of time"""
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
            correlation=correlation, spw='', coloraxis = 'field', width=width,
            symbolsize=5, plotrange=[-1,-1, min_elev, max_elev],  
            averagedata=True, avgtime=avgtime, plotfile = plot_file,
            expformat = 'png', customsymbol = True, symbolshape = 'circle',
            overwrite=True, showlegend=False, showgui=showgui)

def plot_ants():
    """ Plots the layout of the antennae during the observations"""
    plots_obs_dir = './plots/'
    makedir(plots_obs_dir)
    plot_file = plots_obs_dir+'{0}_antpos.png'.format(msfile)
    logger.info('Plotting antenna positions to: {}'.format(plot_file))
    plotants(vis=msfile,figfile=plot_file)

def base_flags(config):
    """ Sets basic initial data flags"""
    flag = config['flagging']
    tol = flag['shadow_tol'] 
    quack_int = flag['quack_int']
    flag_version = 'base_flags'
    logger.info('Flagging antennae with more than {} m of shadowing.'.format(tol))
    flagdata(vis=msfile, mode='shadow', tolerance=tol, flagbackup=False)
    logger.info('Flagging zero amplitude data.')
    flagdata(vis=msfile, mode='clip', clipzeros=True, flagbackup=False)
    logger.info('Flagging first {} s of every scan.'.format(quack_int))
    flagdata(vis=msfile, mode='quack', quackinterval=quack_int, quackmode='beg', flagbackup=False)
    logger.info('Saving flag version as: {}.'.format(flag_version))
    flagmanager(vis=msfile, mode='save', versionname=flag_version)

def tfcrop():
    """ Runs CASA's TFcrop flagging algorithm"""
    flag_version = 'tfcrop'
    logger.info('Running TFCrop.')
    flagdata(vis=msfile, mode='tfcrop', action='apply', display='', flagbackup=False)
    logger.info('Saving flag version as: {}.'.format(flag_version))
    flagmanager(vis=msfile, mode='save', versionname=flag_version)

def rflag(config):
    """ Runs CASA's rflag flagging algorithm"""
    flag = config['flagging']
    flag_version = 'rflag'
    thresh = flag['rthresh']
    logger.info('Running rflag with a threshold of {}.'.format(thresh))
    flagdata(vis=msfile, mode='rflag', action='apply', datacolumn='corrected', 
             freqdevscale=thresh, timedevscale=thresh, display='', flagbackup=False)
    logger.info('Saving flag version as: {}.'.format(flag_version))
    flagmanager(vis=msfile, mode='save', versionname=flag_version)

def extend_flags():
    """ Extends existing flags"""
    flag_version = 'extended'
    logger.info('Extending existing flags.')
    flagdata(vis=msfile, mode='extend', spw='', extendpols=True, action='apply', display='',
             flagbackup=False)
    flagdata(vis=msfile, mode='extend', spw='', growtime=75.0, growfreq=90.0, action='apply',
             display='', flagbackup=False)

def flag_sum(name):
    """ Writes a summary of the current flags to file"""
    plots_obs_dir = './plots/'
    makedir(plots_obs_dir)
    out_file = plots_obs_dir+'{0}_{1}_flags.summary'.format(msfile,name)
    logger.info('Writing flag summary to: {}.'.format(out_file))
    flag_info = flagdata(vis=msfile, mode='summary')
    out_file = open(out_file, 'w')
    out_file.write('Total flagged data: {:.2%}\n\n'.format(flag_info['flagged']/flag_info['total']))
    logger.info('Total flagged data: {:.2%}'.format(flag_info['flagged']/flag_info['total']))
    out_file.write('Flagging per spectral window\n')
    for spw in flag_info['spw'].keys():
        out_file.write('SPW {0}: {1:.2%}\n'.format(spw,flag_info['spw'][spw]['flagged']/flag_info['spw'][spw]['total']))
    out_file.write('\nFlagging per field\n')
    for field in flag_info['field'].keys():
        out_file.write('{0}: {1:.2%}\n'.format(field,flag_info['field'][field]['flagged']/flag_info['field'][field]['total']))
    out_file.write('\nFlagging per antenna\n')
    for ant in flag_info['antenna'].keys():
        out_file.write('{0}: {1:.2%}\n'.format(ant,flag_info['antenna'][ant]['flagged']/flag_info['antenna'][ant]['total']))
    out_file.close()

def select_refant(config,config_raw,config_file):
    """ Checks if a reference antenna to be set, if it has not been the the user is queried"""
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
            print('Valid antenna names:\n{}\n'.format(ant_names))
            calib['refant'] = str(raw_input('Please select a reference antenna by name: '))
            first += 1
        logger.info('Updating config file ({0}) to set reference antenna as {1}.'.format(config_file,calib['refant']))
        config_raw.set('calibration','refant',calib['refant'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    else:
        logger.info('Reference antenna already set as: {}.'.format(calib['refant']))

def set_fields(config,config_raw,config_file):
    """ Checks if the field intentions have already been set, if not then the user is queried"""
    calib = config['calibration']
    tb.open(msfile+'/FIELD')
    field_names = tb.getcol('NAME')
    tb.close()
    change_made = False
    if calib['fluxcal'] not in field_names:
        logger.warning('No valid flux calibrator set. Requesting user input.')
        first = 0
        print('\n\n\n')
        while calib['fluxcal'] not in field_names:
            if first > 0:
                print('\n\nString entered is not a valid field name.')
            print('Valid field names:\n{}\n'.format(field_names))
            calib['fluxcal'] = str(raw_input('Please select a flux calibrator by name: '))
            first += 1
        change_made = True
        logger.info('Flux calibrator set as: {}.'.format(calib['fluxcal']))
    else:
        logger.info('Flux calibrator already set as: {}.'.format(calib['fluxcal']))
    if calib['fluxmod'] == '':
        logger.warning('No valid flux calibrator model set. Requesting user input.')
        print('Usual flux calibrator models will be 3C48_L.im, 3C138_L.im, or 3C286_L.im.\n')
        resp = ''
        while True:
            calib['fluxmod'] = str(raw_input('Please select a flux calibrator model by name: '))
            if calib['fluxmod'] in ['3C48_L.im', '3C138_L.im', '3C286_L.im']:
                break
            else:
                resp = str(raw_input('The model name provided is not one of the 3 expected options.\nDo you want to proceed with the model {} ?'.format(calib['fluxmod'])))
                if resp.lower() not in ['yes','ye','y']:
                    break
                else:
                    continue
        change_made = True
        logger.info('Flux calibrator model set as: {}.'.format(calib['fluxmod']))
    else:
        logger.info('Flux calibrator model already set as: {}.'.format(calib['fluxmod']))
    if calib['bandcal'] not in field_names:
        logger.warning('No valid bandpass calibrator set. Requesting user input.')
        first = 0
        print('\n\n\n')
        while calib['bandcal'] not in field_names:
            if first > 0:
                print('\n\nString entered is not a valid field name.')
            print('Valid field names:\n{}\n'.format(field_names))
            calib['bandcal'] = str(raw_input('Please select a bandpass calibrator by name: '))
            first += 1
        change_made = True
        logger.info('Bandpass calibrator set as: {}.'.format(calib['bandcal']))
    else:
        logger.info('Bandpass calibrator already set as: {}.'.format(calib['bandcal']))
    if calib['phasecal'] not in field_names:
        logger.warning('No valid phase calibrator set. Requesting user input.')
        first = 0
        print('\n\n\n')
        while calib['phasecal'] not in field_names:
            if first > 0:
                print('\n\nString entered is not a valid field name.')
            print('Valid field names:\n{}\n'.format(field_names))
            calib['phasecal'] = str(raw_input('Please select a phase calibrator by name: '))
            first += 1
        change_made = True
        logger.info('Phase calibrator set as: {}.'.format(calib['phasecal']))
    else:
        logger.info('Phase calibrator already set as: {}.'.format(calib['phasecal']))
    if len(calib['targets']) == 0:
        logger.warning('No taregt field(s) set. Requesting user input.')
        print('\n\n\n')
        while True:
            target = ''
            print('Valid field names:\n{}\n'.format(field_names))
            target = str(raw_input('Please select a target field by name: '))
            if target not in field_names:
                print('\n\nString entered is not a valid field name.')
                continue
            else:
                calib['targets'].append(target)
                logger.info('{} set as a target field.'.format(target))
                resp = ''
                while (resp.lower() not in ['yes','ye','y']) and (resp.lower() not in ['no','n']) :
                    resp = str(raw_input('Do you want to add another target (y/n): '))
                if resp.lower() in ['yes','ye','y']:
                    continue
                else:
                    break
        change_made = True
    else:
        logger.info('Target field(s) already set as: {}.'.format(calib['targets']))
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

def calibration(config):
    """ Runs the basic calibration steps"""
    plots_obs_dir = './plots/'
    makedir(plots_obs_dir)
    calib = config['calibration']
    
    gctab = 'gaincurve.cal'
    logger.info('Calibrating gain vs elevation({}).'.format(gctab))
    #gencal(vis=msfile, caltable=gctab, caltype='gceff')
    command = "gencal(vis='{0}', caltable='{1}', caltype='gceff')".format(msfile,gctab)
    logger.info('Executing command: '+command)
    exec(command)
    
    logger.info('Load model for flux calibrator ({}).'.format(calib['fluxmod']))
    #setjy(vis=msfile, field=calib['fluxcal'], spw='', scalebychan=True, model=calib['fluxmod'])
    command = "setjy(vis='{0}', field='{1}', spw='', scalebychan=True, model='{2}')".format(msfile,calib['fluxcal'],calib['fluxmod'])
    logger.info('Executing command: '+command)
    exec(command)
    
    plot_file = plots_obs_dir+'{0}_bpphaseint.png'.format(msfile)
    logger.info('Plotting bandpass phase vs. time for reference antenna to: {}'.format(plot_file))
    plotms(vis=msfile, plotfile=plot_file, xaxis='channel', yaxis='phase', field=calib['bandcal'], correlation='RR', avgtime='1E10', antenna=calib['refant'], coloraxis='antenna', expformat='png', overwrite=True, showlegend=False, showgui=False, exprange='all', iteraxis='spw')
    
    dltab = 'delays.cal'
    logger.info('Calibrating delays for bandpass calibrator ({}).'.format(dltab))
    #gaincal(vis=msfile, field=calib['bandcal'], caltable=dltab, refant=calib['refant'], gaintype='K', gaintable=[gctab])
    command = "gaincal(vis='{0}', field='{1}', caltable='{2}', refant='{3}', gaintype='K', gaintable=['{4}'])".format(msfile,calib['bandcal'],dltab,calib['refant'],gctab)
    logger.info('Executing command: '+command)
    exec(command)
    
    bptab = 'bpphase.gcal'
    logger.info('Make bandpass calibrator phase solutions ({}).'.format(bptab))
    #gaincal(vis=msfile, field=calib['bandcal'],  caltable=bptab, refant=calib['refant'], calmode='p', solint='int', minsnr=2.0, gaintable=[gctab, dltab])
    command = "gaincal(vis='{0}', field='{1}',  caltable='{2}', refant='{3}', calmode='p', solint='int', combine='', minsnr=2.0, gaintable=['{4}','{5}'])".format(msfile,calib['bandcal'],bptab,calib['refant'],gctab,dltab)
    logger.info('Executing command: '+command)
    exec(command)
    
    plot_file = plots_obs_dir+'{0}_bpphasesol.png'.format(msfile)
    logger.info('Plotting bandpass phase solutions to: {}'.format(plot_file))
    plotms(vis=bptab, plotfile=plot_file, gridrows=3, gridcols=3, xaxis='time', yaxis='phase',
           plotrange=[0,0,-180,180], expformat='png', overwrite=True, showlegend=False, showgui=False, exprange='all',
           iteraxis='antenna')
    
    bstab = 'bandpass.bcal'
    logger.info('Determining bandpass solution ({}).'.format(bstab))
    #bandpass(vis=msfile, caltable=bstab, field=calib['bandcal'], refant=calib['refant'], solint='inf', solnorm=True, gaintable=[gctab, dltab, bptab])
    command = "bandpass(vis='{0}', caltable='{1}', field='{2}', refant='{3}', solint='inf', solnorm=True, gaintable=['{4}', '{5}', '{6}'])".format(msfile,bstab,calib['bandcal'],calib['refant'],gctab, dltab, bptab)
    logger.info('Executing command: '+command)
    exec(command)
    
    plot_file = plots_obs_dir+'{0}_bandpasssol.png'.format(msfile)
    logger.info('Plotting bandpass amplitude solutions to: {}'.format(plot_file))
    plotms(vis=bstab, plotfile=plot_file, gridrows=3, gridcols=3, xaxis='chan', yaxis='amp',
           expformat='png', overwrite=True, showlegend=False, showgui=False, exprange='all',
           iteraxis='antenna', coloraxis='corr')
    
    iptab = 'intphase.gcal'
    logger.info('Determining integration phase solutions ({}).'.format(iptab))
    if calib['fluxcal'] == calib['bandcal']:
        calfields = '{0},{1}'.format(calib['bandcal'],calib['phasecal'])
    else:
        calfields = '{0},{1},{2}'.format(calib['bandcal'],calib['fluxcal'],calib['phasecal'])
    #gaincal(vis=msfile, field=calfields, caltable=iptab, refant=calib['refant'], calmode='p', solint='int', minsnr=2.0, gaintable=[gctab, dltab, bstab])
    command = "gaincal(vis='{0}', field='{1}', caltable='{2}', refant='{3}', calmode='p', solint='int', minsnr=2.0, gaintable=['{4}', '{5}', '{6}'])".format(msfile,calfields,iptab,calib['refant'],gctab, dltab, bstab)
    logger.info('Executing command: '+command)
    exec(command)
    
    sptab = 'scanphase.gcal'
    logger.info('Determining scan phase solutions ({}).'.format(sptab))
    #gaincal(vis=msfile, field=calfields, caltable=sptab, refant=calib['refant'], calmode='p', solint='inf', minsnr=2.0, gaintable=[gctab, dltab, bstab])
    command = "gaincal(vis='{0}', field='{1}', caltable='{2}', refant='{3}', calmode='p', solint='inf', minsnr=2.0, gaintable=['{4}', '{5}', '{6}'])".format(msfile,calfields,sptab,calib['refant'],gctab, dltab, bstab)
    logger.info('Executing command: '+command)
    exec(command)
    
    amtab = 'amp.gcal'
    logger.info('Determining amplitude solutions ({}).'.format(amtab))
    #gaincal(vis=msfile, field=calfields, caltable=amtab, refant=calib['refant'], calmode='ap', solint='inf', minsnr=2.0, gaintable=[gctab, dltab, bstab, iptab])
    command = "gaincal(vis='{0}', field='{1}', caltable='{2}', refant='{3}', calmode='ap', solint='inf', minsnr=2.0, gaintable=['{4}', '{5}', '{6}', '{7}'])".format(msfile,calfields,amtab,calib['refant'],gctab, dltab, bstab, iptab)
    logger.info('Executing command: '+command)
    exec(command)
    
    plot_file = plots_obs_dir+'{0}_phasesol.png'.format(msfile)
    logger.info('Plotting phase solutions to: {}'.format(plot_file))
    plotms(vis=amtab, plotfile=plot_file, gridrows=3, gridcols=3, xaxis='time', yaxis='phase',
           expformat='png', overwrite=True, showlegend=False, showgui=False, exprange='all',
           iteraxis='antenna', coloraxis='corr', plotrange=[-1,-1,-20,20])
    
    plot_file = plots_obs_dir+'{0}_ampsol.png'.format(msfile)
    logger.info('Plotting amplitude solutions to: {}'.format(plot_file))
    plotms(vis=amtab, plotfile=plot_file, gridrows=3, gridcols=3, xaxis='time', yaxis='amp',
           expformat='png', overwrite=True, showlegend=False, showgui=False, exprange='all',
           iteraxis='antenna', coloraxis='corr', plotrange=[-1,-1,0,1])
    
    fxtab = 'flux.cal'
    logger.info('Applying flux scale to all calibrators ({}).'.format(fxtab))
    #flux_info = fluxscale(vis=msfile, caltable=amtab, fluxtable=fxtab, reference=calib['fluxcal'], incremental=True)
    command = "fluxscale(vis='{0}', caltable='{1}', fluxtable='{2}', reference='{3}', incremental=True)".format(msfile,amtab,fxtab,calib['fluxcal'])
    logger.info('Executing command: '+command)
    exec('flux_info = '+command)
    
    out_file = plots_obs_dir+'{0}_flux.summary'.format(msfile)
    logger.info('Writing calibrator fluxes summary to: {}.'.format(out_file))
    out_file = open(out_file, 'w')
    for i in range(len(flux_info['spwName'])):
        spw = flux_info['spwName'][i]
        spwID = str(flux_info['spwID'][i])
        out_file.write('Spectral window: {}\n'.format(spw))
        for j in range(len(flux_info)-3):
            fieldID = flux_info.keys()[j]
            out_file.write('Flux density for {0}: {1} +/- {2} Jy\n'.format(flux_info[fieldID]['fieldName'], flux_info[fieldID][spwID]['fluxd'][0], flux_info[fieldID][spwID]['fluxdErr'][0]))
        out_file.write('\n')
    out_file.close()
    
    logger.info('Apply all calibrations to all calibrators and targets.')
    logger.info('Apply applying clibration to: {}'.format(calib['phasecal']))
    #applycal(vis=msfile, field=calib['phasecal'], 
    #         gaintable=[gctab, dltab, bptab, iptab, amtab, fxtab], 
    #         gainfield=['', calib['bandcal'], calib['bandcal'], calib['phasecal'], calib['phasecal'], calib['phasecal']], 
    #         calwt=False)
    command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}', '{7}'], gainfield=['', '{8}', '{8}', '{1}', '{1}', '{1}'], calwt=False)".format(msfile,calib['phasecal'],gctab, dltab, bstab, iptab, amtab, fxtab,calib['bandcal'])
    logger.info('Executing command: '+command)
    exec(command)
    logger.info('Apply applying clibration to: {}'.format(calib['bandcal']))
    #applycal(vis=msfile, field=calib['bandcal'], 
    #         gaintable=[gctab, dltab, bptab, iptab, amtab, fxtab], 
    #         gainfield=['', calib['bandcal'], calib['bandcal'], calib['bandcal'], calib['bandcal'], calib['bandcal']], 
    #         calwt=False)
    command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}', '{7}'], gainfield=['', '{1}', '{1}', '{1}', '{1}', '{1}'], calwt=False)".format(msfile,calib['bandcal'],gctab, dltab, bstab, iptab, amtab, fxtab)
    logger.info('Executing command: '+command)
    exec(command)
    if calib['fluxcal'] != calib['bandcal']:
        logger.info('Applying clibration to: {}'.format(calib['fluxcal']))
        #applycal(vis=msfile, field=calib['fluxcal'], 
        #         gaintable=[gctab, dltab, bptab, iptab, amtab, fxtab], 
        #         gainfield=['', calib['bandcal'], calib['bandcal'], calib['fluxcal'], calib['fluxcal'], calib['fluxcal']], 
        #         calwt=False)
        command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}', '{7}'], gainfield=['', '{8}', '{8}', '{1}', '{1}', '{1}'], calwt=False)".format(msfile,calib['fluxcal'],gctab, dltab, bstab, iptab, amtab, fxtab,calib['bandcal'])
        logger.info('Executing command: '+command)
        exec(command)
    for field in calib['targets']:
        logger.info('Applying clibration to: {}'.format(field))
        #applycal(vis=msfile, field=field, 
        #         gaintable=[gctab, dltab, bptab, iptab, amtab, fxtab], 
        #         gainfield=['', calib['bandcal'], calib['bandcal'], calib['phasecal'], calib['phasecal'], calib['phasecal']], 
        #         calwt=False)
        command = "applycal(vis='{0}', field='{1}', gaintable=['{2}', '{3}', '{4}', '{5}', '{6}', '{7}'], gainfield=['', '{8}', '{8}', '{9}', '{9}', '{9}'], calwt=False)".format(msfile,field,gctab, dltab, bstab, iptab, amtab, fxtab,calib['bandcal'],calib['phasecal'])
        logger.info('Executing command: '+command)
        exec(command)
        
    plot_file = plots_obs_dir+'{0}_corr_phase.png'.format(msfile)
    logger.info('Plotting corrected phases for {0} to: {1}'.format(calib['bandcal'],plot_file))
    plotms(vis=msfile, plotfile=plot_file, field=calib['bandcal'], xaxis='channel', yaxis='phase', ydatacolumn='corrected', correlation='RR', avgtime='1E10', antenna=calib['refant'], coloraxis='antenna2', expformat='png', overwrite=True, showlegend=False, showgui=False)
    
    plot_file = plots_obs_dir+'{0}_corr_amp.png'.format(msfile)
    logger.info('Plotting corrected amplitudes for {0} to: {1}'.format(calib['bandcal'],plot_file))
    plotms(vis=msfile, plotfile=plot_file, field=calib['bandcal'], xaxis='channel', yaxis='amp', ydatacolumn='corrected', correlation='RR', avgtime='1E10', antenna=calib['refant'], coloraxis='antenna2', expformat='png', overwrite=True, showlegend=False, showgui=False)


def split_fields(config):
    calib = config['calibration']
    for field in calib['targets']:
        logger.info('Splitting {0} into separate file: {1}.'.format(field, field+'.split'))
        split(vis=msfile, outputvis=field+'.split', field=field)
        
def contsub(config,config_raw,config_file):
    contsub = config['continuum_subtraction']
    calib = config['calibration']
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
    else:
        print('Current line free channels set as:')
        for i in range(len(contsub['linefree_ch'])):
            print('{0}: {1}'.format(calib['targets'][i],contsub['linefree_ch'][i]))
        resp = str(raw_input('Do you want revise the line free channels (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_ch = True
    if reset_ch:
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
        logger.info('Subtracting the continuum from field: {}'.format(target))
        uvcontsub(vis=target+'.split', field=target, fitspw=chans,
                  excludechans=False,combine='',solint='int', fitorder=contsub['fitorder'], want_cont=contsub['save_cont'])

def plot_spec(config):
    plots_obs_dir = './plots/'
    makedir(plots_obs_dir)
    calib = config['calibration']
    targets = calib['targets']
    for target in targets:
        tb.open('{}.split/SPECTRAL_WINDOW'.format(target))
        nspw = len(tb.getcol('NAME'))
        tb.close()
        for i in range(nspw):
            plot_file = plots_obs_dir+'{0}_amp_chn_spw{1}.png'.format(target,i)
            logger.info('Plotting amplitude vs channel to {}'.format(plot_file))
            plotms(vis=target+'.split.contsub', xaxis='chan', yaxis='amp',
                   ydatacolumn='corrected', spw=str(i), plotfile=plot_file,
                   expformat='png', overwrite=True, showgui=False)
            plot_file = plots_obs_dir+'{0}_amp_vel_spw{1}.png'.format(target,i)
            logger.info('Plotting amplitude vs velocity to {}'.format(plot_file))
            plotms(vis=target+'.split.contsub', xaxis='velocity', yaxis='amp',
                   ydatacolumn='corrected', spw=str(i), plotfile=plot_file,
                   expformat='png', overwrite=True, showgui=False,
                   freqframe='BARY', restfreq='1420.405751MHz', veldef='OPTICAL')
            
def dirty_image(config,config_raw,config_file):
    calib = config['calibration']
    contsub = config['continuum_subtraction']
    rest_freq = config['global']['rest_freq']
    targets = calib['targets']
    cln_param = config['clean']
    logger.info('Checking clean parameters for dirty image.')
    reset_cln = False
    if len(cln_param['line_ch']) == 0 or len(cln_param['line_ch']) != len(targets):
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
    else:
        print('Current image channels set as:')
        for i in range(len(cln_param['line_ch'])):
            print('{0}: {1}'.format(targets[i],cln_param['line_ch'][i]))
        resp = str(raw_input('Do you want revise the channels that will be imaged (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln:
        print('For each target enter the channels you want to image in the following format:\nspwID:min_ch~max_ch')
        for i in range(len(targets)):
            print('Note: The continuum channels for this target were set to: {}'.format(contsub['linefree_ch'][i]))
            cln_param['line_ch'][i] = uinput('Channels to image for {}: '.format(targets[i]), cln_param['line_ch'][i])
            logger.info('Setting image channels for {0} as: {1}.'.format(targets[i], cln_param['line_ch'][i]))
        logger.info('Updating config file to set channels to be imaged.')
        config_raw.set('clean','line_ch',cln_param['line_ch'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    logger.info('Line free channels set as: {}.'.format(cln_param['line_ch']))
    logger.info('For the targets: {}.'.format(targets))
    reset_cln = False
    if len(cln_param['pix_size']) == 0 or len(cln_param['pix_size']) != len(targets):
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
    else:
        print('Current pixel sizes set as:')
        for i in range(len(cln_param['pix_size'])):
            print('{0}: {1}'.format(targets[i],cln_param['pix_size'][i]))
        resp = str(raw_input('Do you want revise the pixel sizes (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln:
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
    else:
        print('Current images sizes set as:')
        for i in range(len(cln_param['im_size'])):
            print('{0}: {1}'.format(targets[i],cln_param['im_size'][i]))
        resp = str(raw_input('Do you want revise the image sizes (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln:
        print('For each target enter the desired image size:')
        for i in range(len(targets)):
            print('Note: The pixel size for this target was set to: {}'.format(cln_param['pix_size'][i]))
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
        tclean(vis=target+'.split.contsub', field=target, 
               spw=cln_param['line_ch'][i], imagename=target+'.dirty',
               cell=cln_param['pix_size'][i], 
               imsize=[cln_param['im_size'][i],cln_param['im_size'][i]],
               specmode='cube', outframe='bary', veltype='radio',
               restfreq=rest_freq, gridder='wproject', wprojplanes=128,
               pblimit=0.1, normtype='flatnoise', deconvolver='hogbom', restoringbeam='common', weighting='briggs',
               robust=cln_param['robust'], niter=0,
               interactive=False)
        
def noise_est(config):
    targets = config['calibration']['targets']
    cln_param = config['clean']
    noise = []
    for target in targets:
        msmd.open(target+'.split.contsub')
        N = msmd.nantennas()
        t_int = msmd.effexposuretime()['value']
        ch_wid = numpy.mean(msmd.chanwidths(0))
        #Note: The above line may cause issues if different spectral windows
        #have very difference frequency resolutions
        msmd.close()
        corr_eff = cln_param['corr_eff']
        SEFD = cln_param['sefd']
        N_pol = 2.
        noise.append(SEFD/(corr_eff*numpy.sqrt(N_pol*N*(N-1)*t_int*ch_wid)))
    return noise

def image(config,config_raw,config_file):
    noises = noise_est(config)
    calib = config['calibration']
    contsub = config['continuum_subtraction']
    rest_freq = config['global']['rest_freq']
    targets = calib['targets']
    cln_param = config['clean']
    logger.info('Beginning generation of clean image(s).')
    if cln_param['multiscale']:
        algorithm = 'multiscale'
        logger.info('Setting CLEAN algorithm to MS-CLEAN.')
        reset_cln = False
        if cln_param['scales'] == []:
            reset_cln = True
            logger.info('MS-CLEAN scales not set. Requesting user input.')
        elif 0 not in cln_param['scales']:
            logger.warning('MS-CLEAN scales do not include point sources. This is highly recommended.')
            resp = str(raw_input('Do you want revise MS-CLEAN scales (y/n): '))
            if resp.lower() in ['yes','ye','y']:
                reset_cln = True
        if reset_cln:
            print('Current scales set to: {} beam diameters.'.format(cln_param['scales']))
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
        ia.open(target+'.dirty.image')
        rest_beam = ia.restoringbeam()
        ia.close()
        reset_cln = False
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
            print('Beam dimensions:')
            print('Major: {0:.2f} {1}'.format(rest_beam['major']['value'],rest_beam['major']['unit']))
            print('Minor: {0:.2f} {1}'.format(rest_beam['minor']['value'],rest_beam['minor']['unit']))
            print('Pixel size: {}'.format(cln_param['pix_size']))
            resp = str(raw_input('Do you want revise the pixel size (y/n): '))
            if resp.lower() in ['yes','ye','y']:
                reset_cln = True
        if reset_cln:
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
            scales = list(numpy.array(numpy.array(scales)*pix_per_beam,dtype='int'))
            max_scales = [36., 120., 970., 970.] #arcsec 
            #For VLA A, B, C, and D array respectively
            #science.nrao.edu/facilities/vla/docs/manuals/oss/performance/resolution
            if 'arcsec' not in cln_param['pix_size'][i]:
                logger.warning('Pixel size not in arcsec. Maximum scale not checked.')
            else:
                pix_size = cln_param['pix_size'][i]
                pix_size = float(pix_size[:pix_size.find('arcsec')])
                if max(scales)*pix_size > max_scales[3]:
                    #THE ABOVE LINE MUST BE CHANGED
                    #THERE NEEDS TO BE AN AUTOMATIC ASSIGNMENT OF ARRAY
                    logger.warning('Some MS-CLEAN scale(s) is (are) larger than largest recoverable angular scales.')
                    logger.info('Removing offending scales.')
                    inx = numpy.where(numpy.array(scales)*pix_size <= max_scales[3])[0]
                    scales = scales[inx]
            logger.info('CLEANing with scales of {} pixels.'.format(scales))
        logger.info('CLEANing {0} to a threshold of {1} Jy.'.format(target,noises[i]*cln_param['thresh']))
        tclean(vis=target+'.split.contsub', field=target, 
               spw=cln_param['line_ch'][i], imagename=target,
               cell=cln_param['pix_size'][i], 
               imsize=[cln_param['im_size'][i],cln_param['im_size'][i]],
               specmode='cube', outframe='bary', veltype='radio',
               restfreq=rest_freq, gridder='wproject', wprojplanes=128,
               pblimit=0.1, normtype='flatnoise', deconvolver=algorithm,
               scales=scales,
               restoringbeam='common', pbcor=True, weighting='briggs',
               robust=cln_param['robust'], niter=100000, gain=0.1,
               threshold='{}Jy'.format(noises[i]*cln_param['thresh']),
               usemask='auto-multithresh', sidelobethreshold=cln_param['automask_sl'],
               noisethreshold=cln_param['automask_ns'], lownoisethreshold=cln_param['automask_lns'],
               minbeamfrac=cln_param['automask_mbf'], negativethreshold=cln_param['automask_neg'],
               cyclefactor=5.0,interactive=False)
        logger.info('CLEANing finished. Image cube saved as {}.'.format(target+'.image'))
        ia.open(target+'.dirty.image')
        coords = ia.coordsys()
        if 'J2000' not in coords.referencecode()[0]:
            logger.info('Coordinate system not J2000. Image will be regridded.')
            imregrid(imagename=target+'.image', template='J2000', 
                     output=target+'.image.J2000', asvelocity=True,
                     interpolation='linear', decimate=10,
                     overwrite=True)
            logger.info('{} regridded in J2000 coordinates.'.format(target+'.image.J2000'))
            imregrid(imagename=target+'.image.pbcor', template='J2000', 
                     output=target+'.image.pbcor.J2000', asvelocity=True,
                     interpolation='linear', decimate=10,
                     overwrite=True)
            logger.info('{} regridded in J2000 coordinates.'.format(target+'.image.pbcor.J2000'))
        coords.done()
        ia.close()

######################   Processing   ####################
# Read configuration file with parameters
config_file = sys.argv[-1]
config,config_raw = read_config(config_file)

# Set up your logger
logger = get_logger(LOG_FILE_INFO  = '{}_log.log'.format(config['global']['project_name']),
                    LOG_FILE_ERROR = '{}_errors.log'.format(config['global']['project_name'])) # Set up your logger

# Start processing
msfile = '{0}.ms'.format(config['global']['project_name'])

# 1. Import data and write listobs to file
'''data_path = config['importdata']['data_path']
data_files = glob.glob(os.path.join(data_path, '*'))
import_data(data_files, msfile)
msinfo = get_msinfo(msfile)

# 2. Diagnostic plots
plot_elevation(config)
plot_ants()

# 3. Apply baisc flags
base_flags(config)
tfcrop()
flag_sum('initial')

# 4. Calibration
select_refant(config,config_raw,config_file)
set_fields(config,config_raw,config_file)
calibration(config)
rflag(config)
flag_sum('rflag')
extend_flags()
flag_sum('extended')
flag_sum('final')
calibration(config)'''

#5. Split, continuum subtract and make dirty image
split_fields(config)
contsub(config,config_raw,config_file)
plot_spec(config)
dirty_image(config,config_raw,config_file)

#6. Clean and regrid (if necessary) image
image(config,config_raw,config_file)
