import imp, numpy, glob, shutil
imp.load_source('common_functions','common_functions.py')
import common_functions as cf


def noise_est(config,logger):
    """
    Makes an estimate of the theortically expected noise level for each science target.
    
    Input:
    config = The parameters read from the configuration file. (Ordered dictionary)
    
    Output:
    noise = Estimate of the theortical noise in Jy/beam. (List of Floats)
    """
    logger.info('Starting making noise estimation.')
    targets = config['calibration']['target_names'][:]
    calib = config['calibration']
    if calib['mosaic']:
        targets = list(set(calib['target_names']))
    cln_param = config['clean']
    src_dir = config['global']['src_dir']+'/'
    noise = []
    for target in targets:
        msmd.open(src_dir+target+'.split.contsub')
        N = msmd.nantennas()
        t_int = msmd.effexposuretime()['value']
        t_unit = msmd.effexposuretime()['unit']
        if t_unit != 's' and 'sec' not in t_unit:
            logger.warning('Integration time units are not in seconds. Estimated noise may be incorrect.')
        ch_wid = numpy.mean(msmd.chanwidths(0))
        #Note: The above line may cause issues if different spectral windows
        #have very difference frequency resolutions
        corr_eff = cln_param['corr_eff']
        SEFD = cln_param['sefd']
        N_pol = 2.
        noise.append(SEFD/(corr_eff*numpy.sqrt(N_pol*N*(N-1.)*t_int*ch_wid)))
        logger.info('Effective integration time for {0}: {1} {2}'.format(target,int(t_int),msmd.effexposuretime()['unit']))
        logger.info('Expected rms noise for {0}: {1} Jy/beam'.format(target,SEFD/(corr_eff*numpy.sqrt(N_pol*N*(N-1.)*t_int*ch_wid))))
        msmd.close()
    logger.info('Completed making noise estimation.')
    return noise


def moment0(config,config_raw,config_file,logger):
    """
    Generates a moment zero map of each science target.
    
    Input:
    config = The parameters read from the configuration file. (Ordered dictionary)
    config_raw = The instance of the parser.
    config_file = Path to configuration file. (String)
    """
    noises = noise_est(config,logger)
    cln_param = config['clean']
    calib = config['calibration']
    if config_raw.has_option('clean','noise'):
        noises = cln_param['noise'][:]
        logger.info('Noise level(s) set manually as {0} Jy.'.format(noises))
    moment = config['moment']
    thresh = moment['mom_thresh']
    chans = moment['mom_chans']
    targets = config['calibration']['target_names']
    if calib['mosaic']:
        targets = list(set(targets))
    img_dir = config['global']['img_dir']+'/'
    mom_dir = config['global']['mom_dir']+'/'
    cf.makedir('./'+mom_dir,logger)
    
    change_made = False
    if len(chans) == 0 or len(chans) != len(targets):
        if len(chans) < len(targets):
            logger.warning('There are more target fields than channel ranges for moments.')
            while len(chans) < len(targets):
                chans.append('')
        elif len(chans) > len(targets):
            logger.warning('There are more moment channel ranges than target fields.')
            logger.info('Current channel ranges: {}'.format(chans))
            logger.warning('The channel range list will now be truncated to match the number of targets.')
            chans = chans[:len(targets)]
        change_made = True
    if interactive:
        print('Current moment channel ranges set as:')
        print(chans)
        print('For the targets:')
        print(targets)
        resp = ''
        while (resp.lower() not in ['yes','ye','y']) and (resp.lower() not in ['no','n']) :
            resp = str(raw_input('Do you want to revise these channel ranges (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            change_made = True
            print('Please specify the channel ranges in the format: chan1~chan2.')
            for i in range(len(chans)):
                chans[i] = cf.uinput('Enter channel range for target {}: '.format(targets[i]), chans[i])
        else:
            pass
    if change_made:
        logger.info('Updating config file to set new moment channel ranges.')
        config_raw.set('moment','mom_chans',chans)
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
        
    logger.info('Starting generation of moment map(s).')
    
    J2000 = False
    img_list = glob.glob(img_dir+'*.image.J2000')
    if len(img_list) > 0:
        J2000 = True
    for i in range(len(targets)):
        if J2000:
            imagename = targets[i]+'.image.J2000'
        else:
            imagename = targets[i]+'.image'
        command = "immoments(imagename='{0}{1}',includepix=[{2},{3}],chans='{4}',outfile='{5}{6}.mom0')".format(img_dir,imagename,thresh*noises[i],thresh*1E6*noises[i],chans[i],mom_dir,targets[i])
        logger.info('Executing command: '+command)
        exec(command)
        cf.check_casalog(config,config_raw,logger,casalog)
        command = "exportfits(imagename='{0}{1}.mom0', fitsimage='{0}{1}.mom0.fits',overwrite=True,dropstokes=True,stokeslast=True,history=True,dropdeg=True)".format(mom_dir,targets[i])
        logger.info('Executing command: '+command)
        exec(command)
        cf.check_casalog(config,config_raw,logger,casalog)
    logger.info('Completed generation of moment map(s).')
    

    
    
# Read configuration file with parameters
config_file = sys.argv[-1]
config,config_raw = cf.read_config(config_file)
interactive = config['global']['interactive']

# Set up your logger
logger = cf.get_logger(LOG_FILE_INFO  = '{}.log'.format(config['global']['project_name']),
                    LOG_FILE_ERROR = '{}_errors.log'.format(config['global']['project_name'])) # Set up your logger

# Define MS file name
msfile = '{0}.ms'.format(config['global']['project_name'])    
    
#Remove previous moment files
cf.check_casaversion(logger)
targets = config['calibration']['target_names']
mom_path = config['global']['mom_dir']+'/'
logger.info('Deleting any existing moment(s).')
for target in targets:
    del_list = glob.glob(mom_path+'*.mom0')
    if len(del_list) > 0:
        for file_path in del_list:
            try:
                shutil.rmtree(file_path)
            except OSError:
                pass
    del_list = glob.glob(mom_path+'*.mom0.fits')
    for file_path in del_list:
        try:
            os.remove(file_path)
        except OSError:
            pass

#Make moment maps
moment0(config,config_raw,config_file,logger)