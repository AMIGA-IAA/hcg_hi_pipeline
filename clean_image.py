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
        f_smo = 1.
        if config_raw.has_option('importdata','hanning'):
            if config['importdata']['hanning']:
                if not config['importdata']['mstransform']:
                    f_smo = 8./3.
                else:
                    if not config_raw.has_option('importdata','chanavg'):
                        f_smo = 8./3.
                    else:
                        Nchan = float(config['importdata']['chanavg'])
                        if Nchan > 1.:
                            f_smo = Nchan/((Nchan-2.) + 2.*(9./16.) + 2.*(1./16.))
                        else:
                            f_smo = 8./3.
        noise.append(SEFD/(corr_eff*numpy.sqrt(f_smo*N_pol*N*(N-1.)*t_int*ch_wid)))
        logger.info('Effective integration time for {0}: {1} {2}'.format(target,int(t_int),msmd.effexposuretime()['unit']))
        logger.info('Expected rms noise for {0}: {1} Jy/beam'.format(target,SEFD/(corr_eff*numpy.sqrt(f_smo*N_pol*N*(N-1.)*t_int*ch_wid))))
        msmd.close()
    logger.info('Completed making noise estimation.')
    return noise

def image(config,config_raw,config_file,logger):
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
    noises = noise_est(config,logger)
    cln_param = config['clean']
    if config_raw.has_option('clean','noise'):
        noises = cln_param['noise'][:]
        logger.info('Noise level(s) set manually as {0} Jy.'.format(noises))
    calib = config['calibration']
    contsub = config['continuum_subtraction']
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
        targets = list(set(targets))
    src_dir = config['global']['src_dir']+'/'
    img_dir = config['global']['img_dir']+'/'
    cf.makedir('./'+img_dir,logger)
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
            print('{0}: {1}'.format(targets[i],cln_param['line_ch'][i]))
        resp = str(raw_input('Do you want revise the channels that will be imaged (y/n): '))
        if resp.lower() in ['yes','ye','y']:
            reset_cln = True
    if reset_cln and interactive:
        print('For each target enter the channels you want to image in the following format:\nspwID:min_ch~max_ch')
        for i in range(len(targets)):
            print('Note: The continuum channels for this target were set to: {}'.format(contsub['linefree_ch'][i]))
            cln_param['line_ch'][i] = cf.uinput('Channels to image for {}: '.format(targets[i]), cln_param['line_ch'][i])
            logger.info('Setting image channels for {0} as: {1}.'.format(targets[i], cln_param['line_ch'][i]))
        logger.info('Updating config file to set channels to be imaged.')
        config_raw.set('clean','line_ch',cln_param['line_ch'])
        configfile = open(config_file,'w')
        config_raw.write(configfile)
        configfile.close()
    logger.info('Line emission channels set as: {}.'.format(cln_param['line_ch']))
    logger.info('For the targets: {}.'.format(targets))
    if numpy.any(cln_param['multiscale']):
        algorithm = 'multiscale'
        logger.info('Setting CLEAN algorithm to MS-CLEAN.')
        if not numpy.all(cln_param['multiscale']):
            logger.info('However, some targets will still use Hogbom CLEAN.')
        reset_cln = False
        if cln_param['beam_scales'] == []:
            reset_cln = True
            logger.warning('MS-CLEAN scales not set.')
        elif 0 not in cln_param['beam_scales']:
            logger.warning('MS-CLEAN scales do not include point sources. This is highly recommended.')
            if interactive:
                resp = str(raw_input('Do you want revise MS-CLEAN scales (y/n): '))
                if resp.lower() in ['yes','ye','y']:
                    reset_cln = True
            else:
                logger.info('Adding point source to MS-CLEAN scales.')
                cln_param['beam_scales'].append(0)
                reset_cln = True
        if reset_cln:
            if interactive:
                print('Current scales set to: {} beam diameters.'.format(cln_param['beam_scales']))
                cln_param['beam_scales'] = cf.uinput('Enter new scales: ', cln_param['beam_scales'])
            logger.info('Setting MS-CLEAN scales as {} beams.'.format(cln_param['beam_scales']))
            logger.info('Updating config file to set MS-CLEAN scales.')
            config_raw.set('clean','scales',cln_param['beam_scales'])
            configfile = open(config_file,'w')
            config_raw.write(configfile)
            configfile.close()
            reset_cln = False
        scales = cln_param['beam_scales']
    else:
        algorithm = 'hogbom'
        logger.info('Setting CLEAN algorithm to Hogbom.')
        scales = None
    for i in range(len(targets)):
        target = targets[i]
        field = fields[i]
        if numpy.all(cln_param['multiscale']):
            ms_clean = True
            algorithm = 'multiscale'
        elif type(cln_param['multiscale']) != type(True):
            ms_clean = cln_param['multiscale'][i]
            if ms_clean:
                algorithm = 'multiscale'
            else:
                algorithm = 'hogbom'
        else:
            ms_clean = False
            algorithm = 'hogbom'
        logger.info('Starting {} image.'.format(target))
        reset_cln = False
        ia.open(img_dir+target+'.dirty.image')
        rest_beam = ia.restoringbeam()
        ia.close()
        if rest_beam['minor']['unit'] not in cln_param['pix_size'][i]:
            logger.error('The pixel size and beam size have diffent units.')
            if ms_clean:
                logger.error('MS-CLEAN scales will likely be incorrect.')
            logger.info('Pixel size: {}'.format(cln_param['pix_size'][i]))
            logger.info('Beam size units: {}'.format(rest_beam['minor']['unit']))
        pix_size = cln_param['pix_size'][i]
        pix_size = float(pix_size[:pix_size.find(rest_beam['minor']['unit'])])
        if pix_size > 0.2*rest_beam['minor']['value']:
            logger.warning('There are fewer than 5 pixels across the beam minor axis. Consider decreasing the pixel size.')
            if interactive:
                print('Beam dimensions:')
                print('Major: {0:.2f} {1}'.format(rest_beam['major']['value'],rest_beam['major']['unit']))
                print('Minor: {0:.2f} {1}'.format(rest_beam['minor']['value'],rest_beam['minor']['unit']))
                print('Pixel size: {}'.format(cln_param['pix_size']))
                resp = str(raw_input('Do you want revise the pixel size (y/n): '))
                if resp.lower() in ['yes','ye','y']:
                    reset_cln = True
        if reset_cln and interactive:
            print('Enter the desired pixel size:')
            cln_param['pix_size'][i] = cf.uinput('Pixel size for {}: '.format(target), cln_param['pix_size'][i])
            logger.info('Setting pixel size for {0} as: {1}.'.format(target, cln_param['pix_size'][i]))
            resp = str(raw_input('Would you also like to revise the image size: '))
            if resp.lower() in ['yes','ye','y']:
                cln_param['im_size'][i] = cf.uinput('Image size for {}: '.format(target), cln_param['im_size'][i])
            logger.info('Setting image size for {0} as: {1}.'.format(target, cln_param['im_size'][i]))
            logger.info('Updating config file to set pixel (image) size.')
            config_raw.set('clean','pix_size',cln_param['pix_size'])
            config_raw.set('clean','im_size',cln_param['im_size'])
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
        if ms_clean:
            pix_size = cln_param['pix_size'][i]
            pix_size = float(pix_size[:pix_size.find(rest_beam['minor']['unit'])])
            pix_per_beam = rest_beam['major']['value']/pix_size
            scales = cln_param['beam_scales']
            scales = list(numpy.array(numpy.array(scales)*pix_per_beam,dtype='int'))
            B_min = au.getBaselineLengths('{0}{1}.split.contsub'.format(src_dir,target), sort=True)[0][1]
            msmd.open('{0}{1}.split.contsub'.format(src_dir,target))
            spws = msmd.spwsforfield(field)
            f_min = None
            for spw in spws:
                if f_min == None or f_min > min(msmd.chanfreqs(spw=spw,unit='Hz')):
                    f_min = min(msmd.chanfreqs(spw=spw,unit='Hz'))
            msmd.close()
            max_scale = 180.*3600.*299792458./(1.2*numpy.pi*f_min*B_min)
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
        if cln_param['automask']:
            mask = 'auto-multithresh'
        else:
            mask = 'pb'
        gridder = 'wproject'
        if calib['mosaic']:
            for target_name in targets:
                inx = [j for j in range(len(calib['target_names'])) if target_name in calib['target_names'][j]]
                fields = numpy.array(calib['targets'],dtype='str')[inx]
            field = ','.join(fields)
            gridder = 'mosaic'
        command = "tclean(vis='{0}{1}'+'.split.contsub', field='{2}', spw='{3}', imagename='{4}{1}', cell='{5}', imsize=[{6},{6}], specmode='cube', outframe='bary', veltype='radio', restfreq='{7}', gridder='{8}', wprojplanes=-1, pblimit=0.1, normtype='flatnoise', deconvolver='{9}', scales={10}, restoringbeam='common', pbcor=True, weighting='briggs', robust={11}, niter=100000, gain=0.1, threshold='{12}Jy', usemask='{13}', phasecenter='{14}', sidelobethreshold={15}, noisethreshold={16}, lownoisethreshold={17}, minbeamfrac={18}, negativethreshold={19}, cyclefactor=2.0,interactive=False)".format(src_dir,target,field,cln_param['line_ch'][i],img_dir,cln_param['pix_size'][i],cln_param['im_size'][i],rest_freq,gridder,algorithm,scales,cln_param['robust'],noises[i]*cln_param['thresh'],mask,cln_param['phasecenter'],cln_param['automask_sl'],cln_param['automask_ns'],cln_param['automask_lns'],cln_param['automask_mbf'],cln_param['automask_neg'])
        logger.info('Executing command: '+command)
        exec(command)
        cf.check_casalog(config,config_raw,logger,casalog)
        logger.info('CLEANing finished. Image cube saved as {}.'.format(target+'.image'))
        ia.open(img_dir+target+'.dirty.image')
        coords = ia.coordsys()
        coord_chn = False
        if 'J2000' not in coords.referencecode()[0]:
            coord_chn = True
            logger.info('Coordinate system not J2000. Image will be regridded.')
            command = "imregrid(imagename='{0}{1}'+'.image', template='J2000', output='{0}{1}'+'.image.J2000', asvelocity=True, interpolation='linear', decimate=10, overwrite=True)".format(img_dir,target)
            logger.info('Executing command: '+command)
            exec(command)
            cf.check_casalog(config,config_raw,logger,casalog)
            logger.info('{} regridded in J2000 coordinates.'.format(target+'.image.J2000'))
            command = "imregrid(imagename='{0}{1}'+'.image.pbcor', template='J2000', output='{0}{1}'+'.image.pbcor.J2000', asvelocity=True, interpolation='linear', decimate=10, overwrite=True)".format(img_dir,target)
            logger.info('Executing command: '+command)
            exec(command)
            cf.check_casalog(config,config_raw,logger,casalog)
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
        cf.check_casalog(config,config_raw,logger,casalog)
        fitsname = target+'_HI.pbcor.fits'
        logger.info('Saving primary beam corrected image cube as {}'.format(fitsname))
        if coord_chn:
            imagename = target+'.image.pbcor.J2000'
        else:
            imagename = target+'.image.pbcor'
        command = "exportfits(imagename='{0}{1}', fitsimage='{0}{2}', velocity=True,optical=False,overwrite=True,dropstokes=True,stokeslast=True,history=True,dropdeg=True)".format(img_dir,imagename,fitsname)
        logger.info('Executing command: '+command)
        exec(command)
        cf.check_casalog(config,config_raw,logger,casalog)
        coord_chn = False
    logger.info('Completed generation of clean image(s).')
    
    
# Read configuration file with parameters
config_file = sys.argv[-1]
config,config_raw = cf.read_config(config_file)
interactive = config['global']['interactive']

# Set up your logger
logger = cf.get_logger(LOG_FILE_INFO  = '{}.log'.format(config['global']['project_name']),
                    LOG_FILE_ERROR = '{}_errors.log'.format(config['global']['project_name'])) # Set up your logger

# Define MS file name
msfile = '{0}.ms'.format(config['global']['project_name'])

#Remove previous image files
targets = config['calibration']['target_names']
img_path = config['global']['img_dir']+'/'
cf.check_casaversion(logger)
logger.info('Deleting any existing clean image(s).')
for target in targets:
    del_list = [img_path+target+'.mask',img_path+target+'.model',img_path+target+'.pb',img_path+target+'.psf',img_path+target+'.residual',img_path+target+'.sumwt',img_path+target+'.weight']
    del_list.extend(glob.glob(img_path+'{}.image*'.format(target)))
    if len(del_list) > 0:
        for file_path in del_list:
            try:
                shutil.rmtree(file_path)
            except OSError:
                pass
    del_list = [img_path+target+'_HI.fits',img_path+target+'_HI.pbcor.fits']
    for file_path in del_list:
        try:
            os.remove(file_path)
        except OSError:
            pass
            
#Make clean image
image(config,config_raw,config_file,logger)

#Review and backup parameters file
cf.diff_pipeline_params(config_file,logger)
cf.backup_pipeline_params(config_file,logger)
