import sys

vis = sys.argv[3]
fields = sys.argv[4]
ampmax = sys.argv[5]

command = "plotms(vis='{0}', gridrows=2, gridcols=2, xaxis='time', yaxis='amp',  field='{1}', iteraxis='baseline', exprange='all', xselfscale=True, yselfscale=True, plotrange=[0.,{2},0.,0.], plotfile='plots/baseline_plots/baseline_plot.png', showgui=False)".format(vis,fields,ampmax)
exec(command)
