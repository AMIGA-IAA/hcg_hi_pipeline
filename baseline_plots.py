import sys

vis = sys.argv[3]
fields = sys.argv[4]
chanavg = sys.argv[5]
ampmax = sys.argv[6]

command = "plotms(vis='{0}', gridrows=2, gridcols=2, xaxis='time', yaxis='amp', field='{1}', spw='0', avgchannel='{2}', iteraxis='baseline', exprange='all', xselfscale=True, yselfscale=True, plotrange=[0,0,0,{3}], plotfile='plots/baseline_plots/baseline_plot.png', coloraxis='scan', showgui=False)".format(vis,fields,chanavg,ampmax)
exec(command)
