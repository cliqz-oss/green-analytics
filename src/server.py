
## http://jinja.pocoo.org/docs/dev/templates/
## http://flask.pocoo.org/docs/0.10/templating/

## https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API/Using_the_Web_Storage_API


import json
from flask import Flask, jsonify, request, render_template
import os, time
from report import analyze_log


import StringIO

PATH = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__, static_folder='static')

NUM_HOSTS = 5
VALID_HOSTS = ["site{}.com".format(i) for i in range(1,NUM_HOSTS+1)]
TRACKER_HOST = "green-tracker.com"

ACCELERATE = 60

LOGFILE = '{}/{}'.format(PATH,'logs/collect.jl')
logf = open(LOGFILE,'a')

start_time = int(round(time.time() * 1000))

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def any(path):

    ##if path == '/favicon.ico':
    ##    return 'ok'
    pretty_host = request.host.split(':')[0]
    if pretty_host.startswith('www.'):
        pretty_host = pretty_host[4:]

    #if pretty_host == TRACKER_HOST and path == '/greetracker.js':
        ## serve the tracker.js
    #    a=1

    elif pretty_host == TRACKER_HOST:
        if path == 'collect':
            try:
                oo = request.json
                logf.write(json.dumps(oo)+'\n')
                logf.flush()
            except:
                print "Error on collect! {}".format(request.json)
            return jsonify({'ok': True})

        if path == 'frame':
            context = {}
            if ACCELERATE > 1:
                context['accelerate'] = {'speed': ACCELERATE, 'start_time': start_time}

            return render_template('/template_frame.html', context=context)

        elif path == 'reset':
            return render_template('/template_frame_reset.html')

        elif path == 'log2':

            context = analyze_log('{}/{}'.format(PATH,'logs/collect.jl.bkp1'))
            return render_template('/template_log.html', context=context)
        else:
            context = analyze_log(LOGFILE)
            return render_template('/template_log.html', context=context)

    elif pretty_host in VALID_HOSTS:

        context = {}

        if ACCELERATE > 1:
            context['accelerate'] = {'speed': ACCELERATE, 'start_time': start_time}


        context['bg'] = 'bg-color-site-{}'.format(VALID_HOSTS.index(pretty_host)+1)
        context['path'] = request.path
        context['host'] = pretty_host
        if context['path'] == '/':
            context['title'] = pretty_host
        else:
            context['title'] = '{}{}'.format(pretty_host, context['path'])

        context['other_sites'] = [('http://{}/'.format(h), 'Visit site #{}'.format(i))
                                    for h, i in zip(VALID_HOSTS, range(1, NUM_HOSTS+1))]

        context['other_sites'] = context['other_sites'] + [('http://{}/page-10.html'.format(h), 'Page 10 on site #{}'.format(i))
                                    for h, i in zip(VALID_HOSTS, range(1, NUM_HOSTS+1))]

        context['other_pages'] = [('/page-{}.html'.format(i), 'Page {}'.format(i))
                                    for i in range(1,11)]



        return render_template('/template_sites.html', context=context)


if __name__ == '__main__':
    ##app.run(host='0.0.0.0', port=80, processes=4, debug=False)
    app.run(host='0.0.0.0', port=80, processes=12, debug=False)
