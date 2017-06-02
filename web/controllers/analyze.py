from flask import request, render_template
from report import analyze_log

class Analyze():

    def respond(self):
    	LOG_FILE = './logs/collect.jl.bkp1'
    	LOGS_DICT = {}
    	context = analyze_log(LOG_FILE)
    	context['site1'] = 'site1.test.cliqz.com'
        return render_template('dashboard.html', context=context)
