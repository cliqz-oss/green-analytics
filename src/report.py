import json
import sys

def format_ts(ts):
    a = []
    for item in ts:
        a.append('[{}]'.format('\t'.join([str(x) for x in item])))
    return '\n'.join(a)


def analyze_log(filename, debug=False):

    pageload_day = {}
    pageloads = {}
    siteloads = {}
    pagevisits = {}
    sitevisits = {}
    stats = {}
    patterns = {}
    transitions = {}
    goals = {}
    returning = {}
    
    labs1 = ['page_load', 'site_load', 'page_visit_by_hour', 'site_visit_by_hour']
    labs1_objs = [pageloads, siteloads, pagevisits, sitevisits]
    
    l1 = dict(zip(labs1, labs1_objs))
    
    f = open(filename,'r')
    lines = f.readlines()
    f.close()
    
    for line in lines:
        try:
            obj = json.loads(line)
        except Exception as e:
            print "Corrupted line: {}".format(line)
            continue

        ts = obj['ts']

        if ts < stats.get('min_ts','99999999999999999999'):
            stats['min_ts'] = ts
        if ts > stats.get('max_ts','0'):
            stats['max_ts'] = ts

        ts_by_hour = "{}/{}/{} {}h".format(ts[0:4],ts[4:6],ts[6:8],ts[8:10])
        ts_by_day = "{}/{}/{}".format(ts[0:4],ts[4:6],ts[6:8])

        ## changed notation in the middle, suffering from memory loss
        ty = obj.get('type', None) or obj['ty']

        if ty in l1:
            if obj['p'] not in l1[ty]:
                l1[ty][obj['p']] = {}
            l1[ty][obj['p']][ts_by_hour] = l1[ty][obj['p']].get(ts_by_hour,0)+1
            
        ## we need the page_loads per day to evaluate 
        ## the success ratio of the goals
        if ty == 'page_load':
            if obj['p'] not in pageload_day:
                pageload_day[obj['p']] = {}
            pageload_day[obj['p']][ts_by_day] = pageload_day[obj['p']].get(ts_by_day,0)+1

        if ty == 'site_visit_by_hour':
            if obj['p'] not in returning:
                returning[obj['p']] = {}
            if ts_by_hour not in returning[obj['p']]:
                returning[obj['p']][ts_by_hour] = []
            returning[obj['p']][ts_by_hour].append(obj['returning_from_ts'])

        if ty in ['new_all', 'new_month', 'new_day']:
            stats[ty] = stats.get(ty,0) + 1

        if ty in 'pattern_by_hour':
            key = ' >> '.join(obj['p'])
            if key not in patterns:
                patterns[key] = {}
            patterns[key][ts_by_hour] = patterns[key].get(ts_by_hour,0)+1
            
        if ty in 'site_correlation_by_hour':
            key = ' <> '.join(obj['p'])
            if key not in transitions:
                transitions[key] = {}
            transitions[key][ts_by_day] = transitions[key].get(ts_by_day,0)+1
            
        if ty in 'goal':
            key = obj['name']
            if key not in goals:
                goals[key] = {}
            if ts_by_day not in goals[key]:
                goals[key][ts_by_day] = {}
            goals[key][ts_by_day][obj['p'][0]] = goals[key][ts_by_day].get(obj['p'][0], 0) + 1


    ts = stats['min_ts']
    stats['min_ts'] = "{}/{}/{} {}:{}h".format(ts[0:4],ts[4:6],ts[6:8],ts[8:10],ts[10:12])
    ts = stats['max_ts']
    stats['max_ts'] = "{}/{}/{} {}:{}h".format(ts[0:4],ts[4:6],ts[6:8],ts[8:10],ts[10:12])
    context = {'stats': stats}


    
    sv = sorted([(u, sum(v.values())) for u, v in sitevisits.items()], key=lambda x: x[1], reverse=True)
    context['sites'] = []
    for s, num_vis in sv[0:3]:
        timeseries = {}
        num_vis = 0
        num_loads = 0
        for k, v in siteloads[s].items():
            if k not in timeseries:
                timeseries[k] = [0, 0]
            timeseries[k][1] += v
            num_loads += v
        for k, v in sitevisits[s].items():
            if k not in timeseries:
                timeseries[k] = [0, 0]
            timeseries[k][0] += v
            num_vis += v

        timeseries = sorted([(k, v[0], v[1]) for k, v in timeseries.items()], key=lambda x: x[0])
        
        context['sites'].append({'s': s, 'num_visits': num_vis, 'num_loads': num_loads, 'timeseries': format_ts(timeseries)})


    
    sv = sorted([(u, sum(v.values())) for u, v in pagevisits.items()], key=lambda x: x[1], reverse=True)
    context['pages'] = []
    for s, num_vis in sv[0:10]:
        timeseries = {}
        num_vis = 0
        num_loads = 0
        for k, v in pageloads[s].items():
            if k not in timeseries:
                timeseries[k] = [0, 0]
            timeseries[k][1] += v
            num_loads += v
        for k, v in pagevisits[s].items():
            if k not in timeseries:
                timeseries[k] = [0, 0]
            timeseries[k][0] += v
            num_vis += v

        timeseries = sorted([(k, v[0], v[1]) for k, v in timeseries.items()], key=lambda x: x[0])

        context['pages'].append({'s': s, 'num_visits': num_vis, 'num_loads': num_loads, 'timeseries': format_ts(timeseries)})

    sv = sorted([(k, sum(v.values())) for k, v in transitions.items()], key=lambda x: x[1], reverse=True)
    context['correlations'] = []
    for s, num_vis in sv[0:3]:
        timeseries = {}
        for k, v in transitions[s].items():
            if k not in timeseries:
                timeseries[k] = 0
            timeseries[k] += v
        timeseries = sorted([(k, v) for k, v in timeseries.items()], key=lambda x: x[0])
        context['correlations'].append({'s': s, 'num_visits': num_vis, 'timeseries': format_ts(timeseries)})


    sv = sorted([(k, sum(v.values())) for k, v in patterns.items()], key=lambda x: x[1], reverse=True)
    context['patterns'] = []
    for s, num_vis in sv[0:10]:
        timeseries = {}
        for k, v in patterns[s].items():
            if k not in timeseries:
                timeseries[k] = 0
            timeseries[k] += v
        timeseries = sorted([(k, v) for k, v in timeseries.items()], key=lambda x: x[0])
        context['patterns'].append({'s': s, 'num_visits': num_vis, 'timeseries': format_ts(timeseries)})

    context['returning'] = []

    for s in sorted(returning.keys()):
        timeseries = {}
        for k, v in returning[s].items():
            timeseries[k] = ', '.join(sorted(["{}/{}/{} {}h".format(x[0:4],x[4:6],x[6:8],x[8:10]) for x in v]))

        timeseries = sorted([(k, v) for k, v in timeseries.items()], key=lambda x: x[0])

        context['returning'].append({'s': s, 'timeseries': format_ts(timeseries)})

    context['hreturning'] = dict([(item['s'], item['timeseries']) for item in context['returning']])

    context['goals'] = []

    for s in sorted(goals.keys()):

        timeseries = {}
        num_succ = 0
        for k, v in goals[s].items():
            for k2, num in v.items():

                if '{} : {}'.format(k, k2) not in timeseries:
                    timeseries['{} : {}'.format(k, k2)] = [0, 0]
                timeseries['{} : {}'.format(k, k2)][0] += num
                timeseries['{} : {}'.format(k, k2)][1] = pageload_day[k2][k]


                num_succ += num



        timeseries = sorted([(k, v[0], v[0]/float(v[1])) for k, v in timeseries.items()], key=lambda x: x[0])

        context['goals'].append({'s': s, 'num_succ': num_succ, 'timeseries': format_ts(timeseries)})


    if debug:
        import pdb
        pdb.set_trace()
        a=1

    return context
    #import pdb
    #pdb.set_trace()
    #a=1


    ## Report period, from: context['stats']['min_ts'] to: context['stats']['max_ts']
    ## 
    ## In this time, we have seen:
    ## context['stats']['new_all] totally new users, never seen before in any site
    ## context['stats']['dau'] unique users by day (across all sites)
    ## context['stats']['mau] unique users by hour (across all sites)
    ## (*note that the figure might be missleading if you have runned the test for a short time)
    ##
    ## Top 3 Sites by traffic (via uniques)
    ## site1 (pageloads: visits: (uniques) )
    ##      [hour, pageloads, uniques]
    ## site2
    
     
    
    ## Top 5 Sites by traffic
    ## site1 (pageloads: visits: (uniques) )
    ##      [hour, pageloads, uniques]
    ## site2 

if __name__ == '__main__':

    analyze_log(sys.argv[1], debug=True)

