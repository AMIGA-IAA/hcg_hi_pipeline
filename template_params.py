[global]
project_name = ''
append_log = False

[importdata]
data_path = ./raw_data/

[plot_elevation]
correlation = RR
avgtime = 16
min_elev = 0
max_elev = 90
width = 900

[flagging]
shadow_tol = 5.0
quack_int = 5.0
rthresh = 4.0

[calibration]
refant = ''
fluxcal = ''
fluxmod = ''
bandcal = ''
phasecal = ''
targets = []

[continuum_subtraction]
linefree_ch = []
fitorder = 1
save_cont = True

