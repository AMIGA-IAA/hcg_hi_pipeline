import imp, glob, numpy
imp.load_source('common_functions','common_functions.py')
import common_functions as cf

def dirty_cont_image(config,config_raw,config_file,logger):
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
    targets = calib['target_names'][:]
    fields = calib['targets'][:]
    for i in range(len(targets)):
        target = targets[i]
        if 'spw' in target:
            inx = target.index('.spw')
            target_name = target[:inx]
            if target_name in calib['target_names'][i-1]:
                fields.insert(i,fields[i-1])
    if calib['mosaic']:
        targets = list(set(calib['target_names']))
    cln_param = config['clean']
    src_dir = config['global']['src_dir']+'/'
    img_dir = config['global']['img_dir']+'/'
    cf.makedir('/.'+img_dir,logger)
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
            print('{0}: {1}'.format(targets[i],cln_param['pix_size'][i]))
        resp = str(raw_input('Do you want revise the pixel sizes (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln and interactive:
        print('For each target enter the desired pixel size:')
        for i in range(len(targets)):
            cln_param['pix_size'][i] = cf.uinput('Pixel size for {}: '.format(targets[i]), cln_param['pix_size'][i])
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
            print('{0}: {1}'.format(targets[i],cln_param['im_size'][i]))
        resp = str(raw_input('Do you want revise the image sizes (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln and interactive:
        print('For each target enter the desired image size:')
        for i in range(len(targets)):
            print('Note: The pixel size for this target was set to: {}'.format(cln_param['pix_size'][i]))
            cln_param['im_size'][i] = cf.uinput('Image size for {}: '.format(targets[i]), cln_param['im_size'][i])
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
        field = fields[i]
        gridder = 'wproject'
        if calib['mosaic']:
            for target_name in targets:
                inx = [j for j in range(len(calib['target_names'])) if target_name in calib['target_names'][j]]
                fields = numpy.array(calib['targets'],dtype='str')[inx]
            field = ','.join(fields)
            gridder = 'mosaic'
        logger.info('Making dirty image of {} (inc. continuum).'.format(target))
        command = "tclean(vis='{0}{1}.split', field='{2}', imagename='{3}{1}.cont.dirty', cell='{4}', imsize=[{5},{5}], specmode='cube', outframe='bary', veltype='radio', restfreq='{6}', gridder='{7}', wprojplanes=-1, pblimit=0.1, normtype='flatnoise', deconvolver='hogbom', weighting='briggs', robust={8}, niter=0, phasecenter='{9}', interactive=False)".format(src_dir,target,field,img_dir,cln_param['pix_size'][i],cln_param['im_size'][i],rest_freq,gridder,cln_param['robust'],cln_param['phasecenter'])
        logger.info('Executing command: '+command)
        exec(command)  
        cf.check_casalog(config,config_raw,logger,casalog)
    logger.info('Completed making dirty continuum image.')

    
# Read configuration file with parameters
config_file = sys.argv[-1]
config,config_raw = cf.read_config(config_file)
interactive = config['global']['interactive']

# Set up your logger
logger = cf.get_logger(LOG_FILE_INFO  = '{}.log'.format(config['global']['project_name']),
                    LOG_FILE_ERROR = '{}_errors.log'.format(config['global']['project_name'])) # Set up your logger

# Define MS file name
msfile = '{0}.ms'.format(config['global']['project_name'])

#Make dirty continuum image
cf.check_casaversion(logger)
cf.rmdir(config['global']['img_dir'],logger)
dirty_cont_image(config,config_raw,config_file,logger)

#Review and backup parameters file
cf.diff_pipeline_params(config_file,logger)
cf.backup_pipeline_params(config_file,logger)