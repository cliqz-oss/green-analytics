import UAParser from 'ua-parser-js';
import CryptoJS from 'crypto-js';

var loc = window.location;
var collectPath = 'collect';
var endPoint = loc.protocol + "//" + loc.hostname + (loc.port? ":"+loc.port : "") + "/" + collectPath;

var parser = new UAParser();
var ua = parser.getResult();
var siteID = '';

var main = function(urlParse) {

    /*
    Disclaimer: Code here is not particularly clean or at the right level of abstraction.
    Furthermore, it is extremely verbose. Believe it or not this is intentional.
    Take this code snippet as an example to illustrate the gist of green-tracker's approach to build
    privacy preserving analytics, rather than as a example of javascript programming.
    Please bear with it; it's very short and I hope is worthy of your time.
    */

    var url = urlParse.href;
    var now = gtUtils.getDate(); // instead of 'new Date()' because of the stub for accelerated time

    var ref = gtUtils.parseRef(urlParse.ref);

    var timestamp = gtUtils.dateToTimestamp(now);
    var timestamp_by_hour = timestamp.slice(0,10);
    var timestamp_by_day = timestamp.slice(0,8);

    var o = localStorage.getItem('xt:count')
    if (!o) o = 0;
    else o = parseInt(o);
    o+=1;
    localStorage.setItem('xt:count', o)

    //console.log('LS >>>>>' , o, localStorage.length, localStorage.getItem('gt:history'));
    //console.log('SS >>>>>' , sessionStorage.length, sessionStorage.getItem('gt:history'));

    // var tmp = url.replace('http://','').split('/');
    // var site = tmp[0], page = '/'+tmp.splice(1,tmp.length).join('/');
    var site = urlParse.origin;
    var dataToSend = [];

    /*
    these two messages, will always be sent: a page and a site load
    */
    dataToSend.push({ts: timestamp, type: 'page_load', p: url})
    dataToSend.push({ts: timestamp, type: 'site_load', p: site})

    /*
    siteMem will have data related to the site being visited, this site must be using
    green-tracker. Should be obvious but better to be clear:sites that do not include
    green-tracker do not trigger this script.
    */

    var hSite = gtUtils.hashSHA1(site,20);

    /*
    the id of the site is hashed with SHA1 and we only kept the first half. This
    is meant to protect the privacy of the user of someone with physical access to their
    computer. Accessing the localStorage on green-tracker.com would reveal the sites
    that the person has visited. We increase the probability of collision by keeping only
    the first half, but still neglible, and we gained plausible deniability. Everybody
    knows that privacy starts at home :-)
    */

    var siteMem = JSON.parse(localStorage.getItem('gt:site:'+hSite) || "{\"site\": {}, \"urls\": {}}");

    // let's see if we have been in the page before,
    var firstTimestamp = '000000000000';
    var hUrl = gtUtils.hashSHA1(url,20);
    if (!siteMem['urls'][hUrl]) siteMem['urls'][hUrl] = firstTimestamp;

    var diffs = gtUtils.timeDiffPeriods(siteMem['urls'][hUrl], timestamp);
    console.log(diffs);
    /*
    'diffs' will tell us if it's  new visit for different time resolutions, from year to minute.
    To achieve this we only need to compare the current timestamp with the timestamp of the last
    visit to the site/page.

    Basically, if you have already visited the site in this month, day, hour, the message will
    not be added to dataToSent. Consequently green-tracker can be certain that all
    'page_visit_by_*' messages come from different user, without having to know any UID
    about the user. That is the most important concept of green-tracker. The state is not
    on the server-side, therefore, there is not need to the server to identify the user, because
    everything that needs to be aggregated, will be safely aggregated on the client.
    */
    for(var i=0;i<diffs.length;i++) {
        if (diffs[i]!='min') {
            // we exclude the minute because it is not relevant for our analytics use-case,
            // we just wanted to show that is possible to have fine-grain time-resolution.
            dataToSend.push({ts: timestamp, type: 'page_visit_by_'+diffs[i], p: url, ref: ref});
        }
    }
    /*
    note the 'trick', we add to dataToSend (to be sent to green-tracker) the real site, urls, etc.
    However, to maintain the state in the localStorage it suffices to work with the truncated
    hashes
    */
    siteMem['urls'][hUrl] = timestamp;

    if (!siteMem['site']['last_visit']) siteMem['site']['last_visit'] = firstTimestamp;
    var diffs = gtUtils.timeDiffPeriods(siteMem['site']['last_visit'], timestamp);
    for(var i=0;i<diffs.length;i++) {
        if (diffs[i]!='min') {
            var msg = {ts: timestamp, type: 'site_visit_by_'+diffs[i], p: site};
            if (siteMem['site']['last_visit']!=firstTimestamp) msg['returning_from_ts'] = siteMem['site']['last_visit'].slice(0,10);
            /*
            note that this time, in the message to be sent to green tracker we added
            the last time the user visited the site, this way, green-tracker can calculate
            useful analytics like returning rates. This is a case of aggregating data on the client
            side. The message, however, is still safe with regards to privacy.
            */
            dataToSend.push(msg);
        }
    }
    siteMem['site']['last_visit'] = timestamp;

    /*
    To this point, we already send the data to count pageloads (not unique), and visits (uniques)
    by different time resolutions. We must save the object to localStorage. At this point, you
    will probably realize that update is not thread-safe, you are correct, it's on the TODO
    list (any takers?). The link below looks quite promising:
    https://bitbucket.org/balpha/lockablestorage/raw/96b7ddb1962334cde9c647663d0053ab640ec5a1/
    */
    localStorage.setItem('gt:site:'+hSite,JSON.stringify(siteMem));

    var last_visit_in_any_site = localStorage.getItem('gt:last_visit_in_any_site') || firstTimestamp;
    localStorage.setItem('gt:last_visit_in_any_site', timestamp);

    if (last_visit_in_any_site==firstTimestamp) {
        // the user was totally new, never seem him/her before across any site,
        // so we send the message of new_user
        dataToSend.push({ts: timestamp, type: 'new_all'});
    }
    var diffs = gtUtils.timeDiffPeriods(last_visit_in_any_site, timestamp);
    for(var i=0;i<diffs.length;i++) {
        if (diffs[i]!='min') {
            var browser = ua.browser.name;
            var os = ua.os.name;

            dataToSend.push({ts: timestamp, type: 'new_'+diffs[i], browser: browser, os: os, ref: ref});
        }
    }

    /*
    Let's build some more complex use-cases. We might be interested to receive click-through
    pattern. Kind of, people went here, and then there.
    This patterns can be dangerous with regards to privacy, so please, be careful on the
    the length and on not sending patterns that span across different sites. In general,
    cross-site data should never be sent raw, because even if not UID is send, the urls
    on their own can identify the user implicity.

    For instance, I'm on my Facebook account (url1) and click on a link, so I go to url2
    outside Facebook. Let's supposed that both sites use green-tracker.
    If the patterns url1->url2 is sent, it can be the case that an attacker (in this case
    the green-tracker) could learn the identify of the user that visited url2. How?
    If url1 contains a ID of the user I might know his identity, as a matter of fact, if
    the page is only accessible after a signup, or if the url2 does not exists in the
    public version of url1 we can conclude that whoever clicked was the real owner of
    the account. Big privacy leak. Just to be clear that's what happens today in
    virtually any tracker, be it for ads ot for analytics, including GA (as per the example in
    the README.md).

    What if url1->url2 are both in Facebook, doesn't the same attack apply? Yes, but the risk
    is much smaller, and what is more important, the owner of the site has all the control
    to prevent this situation by not using a 3rd party system to track sensitive page his site.
    In case of cross-site, the site owner cannot prevent it in any way, because the destination
    is beyond his control. So, no blanket cross-site patterns when full URLS are involved.

    In this segment of the code we keep a history of the last 10 pages visited if they
    are not older than 1 hour. We must be careful of not keeping more history than strictly
    necessary because we are keeping urls in plain-text, which means that anyone with
    physical access to the computer could see.
    */

    var history = JSON.parse(localStorage.getItem('gt:history') || "[]");
    history.unshift([url, timestamp]);
    history = history.slice(0, 10);
    var tooOld = -1;
    for(var i=1;i<history.length;i++) {
        if (gtUtils.timeDiffMinutes(timestamp, history[i][1]) > 60) {
            tooOld = i;
            break;
        }
    }
    if (tooOld!=-1) history = history.slice(0, tooOld);
    localStorage.setItem('gt:history', JSON.stringify(history));


    /*
    Once we have the history, we can check for fairly complex patterns. Let's
    start with checking if a campaign goal has been achieved.

    All campaign goals tracker by green-tracker must be in the client,
    in this case we only have one. We are tracking visits on page-10 of site4
    (assume is the thank you page after a sign-up) after visiting either
    page-10 in site5 or page-9 on site4 (which could hold ads suggesting you
    to signup).

    Thanks to the history is evident that we can validate if the goal
    has been achieved. In fact, we can add additional conditions such as
    time between start and end to be less than 30 minutes and less than
    4 hops away. Naturally, more sophisticated conditions could apply.

    There are a some considerations when tracking goals.
    All goals observed by the tracker must be explicitly defined in the
    client. Otherwise they could not be reported. Consequently,

    New goals need to be propagated to all client, this is really a problem
    because they can be served via CDN and loaded as an external resource, a
    applying caching, etc.

    However once every so often users will have to download them all, a quick
    back on the envelope calculation yields ~200KB per thousand goals (once on a
    proper structure). That's not that much, but a typical tracker can have
    hundreds of thousands. So goal calculation will become a bit more expensive
    in terms of network transfer but at least you will not be broadcasting
    everywhere you go. It is important to mention too, that nothing prevent
    us too load goals as we visit sites, for instance, after a visit to site1.com
    we could load only goals that apply to that site rather than loading all
    goals.

    From the customer of the tracker, having the goals on the client side also
    raise few concerns. Mostly, a) their inability to do retrospective analysis,
    no way around it. And, b) they might not like to have their campaign goals
    exposed to everyone to see. As a matter of fact, an end-user I would welcome
    this; transparency is always good. However, the companies whose are the customers
    of tracker are also competing among themselves, so too much transparency can
    affect them negatively.

    For the sake of not adding more complexity in this walk-through we will keep
    'campainGoals' as plain text. However it should be evident that both 'target'
    and 'sources' are candidates to be truncated hashes, so that the urls are
    obfuscated to all but the owner of the goal. Furthermore, the 'labels'
    that contain customer specific information can be replaced by ids to be
    resolved at collection time in the server-side.

    Let us stress that campaignGoals should be loaded as an external resource, where
    both urls and labels are obfuscated, instead of declared here in plain text.
    */

    var campaignGoals = [
        {'name': 'signup to site4',
            'target': {
                    'url': 'http://site4.test.cliqz.com/page-10.html',
            },
            'sources': [
                {'url': 'http://site5.test.cliqz.com/page-10.html', 'label': 'external ad #1'},
                {'url': 'http://site4.test.cliqz.com/page-9.html', 'label': 'internal ad #1'}
            ]
        }
    ];

    /*
    Since it is just a demo let us traverse all goals, naturally, this would
    not be efficient enough in a real case scenario where you can have a fair amount
    of goals.
    */
    var cache = JSON.parse(localStorage.getItem('gt:cache_goals') || "{}");

    for(var i=0; i<campaignGoals.length; i++) {
        var goal = campaignGoals[i];
        // We must check if the goal has not been already achieved by the user
        if (!cache[gtUtils.hashSHA1(goal['name'])]) {
            if (goal['target']['url']==history[0][0]) {
                // The user is at the target of the goal,
                // We must check if he has arrived here from the desired sources
                for(var j=1;j<Math.min(4, history.length);j++) {
                    // check maximum of 4 hops
                    var prev = history[j];
                    if (gtUtils.timeDiffMinutes(timestamp, prev[1]) < 30) {
                        // still within 30 minutes
                        for(var z=0;z<goal['sources'].length;z++) {
                            if (goal['sources'][z]['url']==prev[0]) {
                                // found it! the goal has been achieve. Let's put the goal name in the cache
                                // to prevent of reporting it ever again.
                                cache[gtUtils.hashSHA1(goal['name'])] = true;
                                localStorage.setItem('gt:cache_goals', JSON.stringify(cache));
                                var lab = goal['sources'][z]['url'] + ' ' + goal['sources'][z]['label'];
                                dataToSend.push({ts: timestamp, type: 'goal', 'name': goal['name'], 'p': lab});
                                break;
                                j = 4; // force the break of the outer loop.
                            }
                        }
                    }
                    else break;
                }
            }
        }
    }


    /*
    We are done with the campaign goals. Next we will report click-through patterns which are
    also very interesting for site owners to better understand how users interact with their sites.

    For the sake of the example, we will show how we can record a click-through of length 2 or 3, provided
    that there is not cross site links between the pages visited.

    Cross-site relationships are very interesting for site owner too, but they are two dangeours to
    be treated as a click-through. In the example we will see that in the case of a cross-site relationship
    we will only emit the signal that there is a connection between two sites, hiding the actual path
    to preserve the privacy of the user. Basically, the signal will say that someone went from site1 to
    site2, but not the actual urls.
    */

    var tmp_pattern = history.slice(history.length-3, history.length);
    var patterns = [];
    for(var i=0;i<tmp_pattern.length;i++) {
        if (gtUtils.timeDiffMinutes(timestamp, tmp_pattern[i][1]) < 40) {
            // consider pages that were visited within 40 minutes from now,
            patterns.push(tmp_pattern[i][0]);
        }
    }

    var correlations = [];
    if (patterns.length > 0) {
        var num_obfuscated = 0;
        var pivot_site = patterns[0].replace('http://','').split('/')[0];
        for(var i=1;i<patterns.length;i++) {
            var tmp_site = patterns[i].replace('http://','').split('/')[0];
            if (tmp_site!=pivot_site) {
                // The click-through pattern goes across different sites, obfuscate for privacy
                patterns[i] = '(obfuscated)';
                num_obfuscated++;
                // but we want to learn correlations across sites, only site,
                // we can keep that
                correlations.push([pivot_site, tmp_site]);
            }
        }

        var cache = JSON.parse(localStorage.getItem('gt:cache_by_hour') || "{}");

        /*
        add the pattern only if it has at least two items that are not obfuscated
        */
        if ((patterns.length - num_obfuscated) >= 2) {
            var key_pattern_hash = gtUtils.hashSHA1('patterns: '+ patterns.join(' >> '));
            /*
            Has the key been seen in the last hour by the user? If not, then send. This is an
            alternative way to check for uniqueness as the one we presented before when
            dealing with 'page_visit_by_*'
            */
            if (!cache[timestamp_by_hour]) {
                  /*
                if cache[timestamp_by_hour] is undefined means that the cache was empty, never used,
                or the that it contains only old hours. In either case we only want to keep the current
                hour, so we can force init it, and the will remove old hours if existed.

                In the next example we will see a use-case where the data from previous hours is used to
                calculate aggregated statistics like number of page visited and time spend on pages by user.
                */
                cache = {}
                cache[timestamp_by_hour] = {}
            }

            if (!cache[timestamp_by_hour][key_pattern_hash]) {
                // the key is new for the hour
                cache[timestamp_by_hour][key_pattern_hash] = true;
                localStorage.setItem('gt:cache_by_hour', JSON.stringify(cache));
                dataToSend.push({ts: timestamp, type: 'pattern_by_hour', p: patterns});
            }
        }

        /*
        We must repeat the same by the correlations, also bounded by hour
        */
        if (correlations.length>0) {
            // you only want the last one
            var corr = correlations[correlations.length-1];
            var key_correlation_hash = gtUtils.hashSHA1('correlation: '+ corr.join(' >> '));
            if (!cache[timestamp_by_hour]) {
                cache = {}
                cache[timestamp_by_hour] = {}
            }
            if (!cache[timestamp_by_hour][key_correlation_hash]) {
                // the key is new for the hour
                cache[timestamp_by_hour][key_correlation_hash] = true;
                localStorage.setItem('gt:cache_by_hour', JSON.stringify(cache));
                dataToSend.push({ts: timestamp, type: 'site_correlation_by_hour', p: corr});
            }
        }
    }

    /*
    To finish the use-cases let us introduce a last one that is conceptually different.
    Up until now we have used the client state (the localStorage) to mark whether a message,
    a signal, has been already sent to the backend or not.

    The state however can also be used to aggregate data across time by user, for instance,
    we might be interested in knowing the number of different pages loads that a user does
    on a site plus the average time spend on the pages of the site.

    Naturally, we cannot do the aggregation on the server-side, because it would require
    the user to send a UID, thus compromising his privacy. Instead, we will accumulate the
    statistics on the localStorage by the desired time-bucket.

    Regularly, the user will check if there are aggregated statistics whose time-resolution
    has already elapsed; for instance, if we keep the statistics per hour, any statistic
    for previous hours will not change further, so it can be sent.

    This approach is very light-weight but it has a couple of considerations:

    1) In the ideal case we can only send statistics after the time-resolution has elapsed, there
    is a delay on the data received. This issue can be minimized in different ways. First, we can
    send partials, however, that is not very straight-forward to implement properly, and it does
    not completely eliminate the issue. Another solution to combine the aggregation with the
    reporting-like behaviour explained previously. There is no rule against reported aggregates every
    hour, but under certain circumstances report immediately. A typical case would be a system that
    measures the latency of requests. We could aggregate response time statistics to obtain the
    median, 99th, etc. every hour, which will be send once the hour has passed, so 1 hour delay.
    At the same time, we could send a signal if the user experiences more than 5 request with a
    response time above a threshold, thus, obtaining a real-time alert.

    2) The second consideration is that there is no guarantee that the aggregated data will ever
    be sent. There is no guarantee that the aggregated data with a time resolution
    of 1 hour will be send immediately after 1 hour either. Aggregated data will only be sent when
    the user runs this script, and there is no guarantee that the user will run the script ever
    agent. Naturally it is highly unlikely that the script is never run again, since this script
    is mean to be present in many pages of many different sites. Nevertheless, it is something
    that needs to be considered.

    For the site1.com only, to simplify the code, we will report the average number of page-loads
    and the times spend on a page by user by hour. So, the site1.com owner will be able to
    categorize the engagement of his users by pageloads and by time-spend without compromising
    his user's privacy. In fact, the site1.com will be able to measure time spend on the page
    by user without having to resort to put a time-beacon on the users computer; a time-beacon
    typically pings a backend every few seconds to signal that the user is still on a page, this
    approach is very wasteful, in particular on the mobile because the continuous use of the radio
    drains the battery. With the client-side aggregation proposed by Green-tracker, beacons are
    no longer necessary as we will see in the following example.
    */
    // var monitoringSites = ['site1.test.cliqz.com'];

    // if (monitoringSites.indexOf(site)!=-1) {
        // The user is at site1.com, the only site for which we want aggregated statistics per user.
    var cache = JSON.parse(localStorage.getItem('gt:agg_cache_time_by_hour:'+hSite) || "{}");
    if (!cache[timestamp_by_hour]) {
        /*
        It does not exist, either new user or it's a new hour.

        This time we must check if the have old hours with data, if so, we must
        send and remove.
        */
        var pastHours = Object.keys(cache);
        for(var i=0;i<pastHours.length;i++) {
            var x = pastHours[i];
            dataToSend.push({ty: 'agg_'+site, ts: x, o: cache[x]});
            delete cache[x];
        }
        // create the entry for today,
        cache[timestamp_by_hour] = {agg_page_loads: 0, agg_page_time: 0};
    }
    cache[timestamp_by_hour]['agg_page_loads'] += 1;
    localStorage.setItem('gt:agg_cache_time_by_hour:'+hSite, JSON.stringify(cache));
    // }

    /*
    Note that are only aggregating 'agg_page_loads', the aggregation of the time is not done here
    but with the time interval associated to the iframe that can be found a bit below.

    This is only for demo purposes, we store the latest 200 messages in your localStorage
    so that you can see the type of messages that are being send. To see them you can
    check the url: http://green-tracker.com/introspect/messages
    */
    var messagesCap = 200;
    var messages = JSON.parse(localStorage.getItem('gt:message-sent-demo-only') || '[]');
    var messages_to_store_for_demo = dataToSend.reverse().concat(messages).slice(0, messagesCap);
    localStorage.setItem('gt:message-sent-demo-only', JSON.stringify(messages_to_store_for_demo));

    /*
    Finally, the last step is to send the data messages to the green-tracker backend. At this
    point the array dataToSend might contain few message that will be sent individually. They cannot
    be bulked into a single request to green-tracker.com/collect because that would create an
    explict association between the messages.

    Ideally we should send each message with a random interval, to break any temporal correlation
    that green-tracker.com could use to try to guess if the messages come from the same user. This is
    done by design in the case of messages generated from different pages, but for messages from
    the same page it is problematic to add the random interval because once the user leaves the page
    the script will stop running and we risk losing them. What we can do at least is randomize them to
    destroy correlations due to order.
    */

    gtUtils.sendAllPar(gtUtils.shuffleArray(dataToSend));

};


var incomingMsg = function(evt) {

    // The structure of evt is document.location, since we need the origin, path, protocol etc.

    /*
    Called to the main script, 'evt.data' contains the url of the parent document passed
    via postMessage. Because of SOP (Same Origin Policy) iframe from a different origin
    cannot access the parent document for security reasons. In our case, the iframe is loaded
    from green-tracker.com and the parent document is loaded from siteX.com. Thanks to the
    postMessage, however, the siteX.com owner can communicate safely with the iframe, only
    the information that is required, and the iframe is contained, thus, eliminating the
    risk of a miss-behaving iframe.
    */

    var urlParse = evt.data.urlDetails;
    siteID = evt.data.siteID;
    main(urlParse);

    /*
    Because we want to aggregate the visit time per page we will add an interval
    to the iframe document. Every 2 seconds the code below will be executed for as
    long as the iframe exists, that is for as long as the user has the page containing
    the iframe opened.
    */
    setInterval(function() { return function(urlParse) {
        // var tmp = url.replace('http://','').split('/');
        // var site = tmp[0];
        var site = urlParse.origin
        if (['site1.test.cliqz.com'].indexOf(site)!=-1) {
            var now = gtUtils.getDate();
            var timestamp = gtUtils.dateToTimestamp(now);
            var timestamp_by_hour = timestamp.slice(0,10);
            var hSite = gtUtils.hashSHA1(site, 20);

            var cache = JSON.parse(localStorage.getItem('gt:agg_cache_time_by_hour:'+hSite) || "{}");
            var o = cache[timestamp_by_hour];

            if (o && o.hasOwnProperty('agg_page_time')) {
                o['agg_page_time'] += 2;
                localStorage.setItem('gt:agg_cache_time_by_hour:'+hSite, JSON.stringify(cache));
            }
        }
    }(urlParse)},2000);
}

// Check from the where the origin came.
window.addEventListener("message", incomingMsg, false);


/*
From here on we have helpers that do not provide insight into the approach proposed
by green-tracker. To learn about the possibilities and on examples on how to map
your use-case to the client-side aggregation proposed here is found above. Feel free to
add further examples, we would be happy to include them in the documentation.
*/


var gtUtils = (function() {
    var m = {};

    m.getDate = function() {

        return new Date();

    };

    // Check if this funciton is being used.
    m.sendAll = function(arr) {
        (function(arrint) {
            if (arrint.length>0) {
                var xhr = new XMLHttpRequest();
                xhr.open('POST',endPoint);
                xhr.setRequestHeader('Content-Type', 'application/json');
                xhr.onreadystatechange = function () {
                    if (xhr.readyState == 4 && xhr.status == 200) {
                        if (arrint.length > 0) m.sendAll(arrint.slice(1,arrint.length));
                    }
                }
                //console.log('sending',arrint.length, JSON.stringify(arr[0]),JSON.stringify(arrint));
                xhr.send(JSON.stringify(arr[0]));
            }
        })(arr);
    };

    m.sendAllPar = function(arr) {
        (function(arrint) {
            for(var i=0;i<arrint.length;i++) {

                var message = arrint[i];
                message.site_id = siteID;
                var xhr = new XMLHttpRequest();
                xhr.open('POST',endPoint);
                xhr.setRequestHeader('Content-Type', 'application/json');
                xhr.onreadystatechange = function () {}
                xhr.send(JSON.stringify(message));

            }
        })(arr);
    };


    var twoDigits = function(num) {
        num = ''+parseInt(num);
        if (num.length<2) num = '0'+num;
        return num;
    };

    m.hashSHA1 = function(s, truncate) {
        var s2 = CryptoJS.SHA1(s).toString();
        if (truncate) s2 = s2.slice(0, truncate);
        return s2;
    }


    m.timeDiffPeriods = function(ts1, ts2) {
        var labs = ['year','month','day','hour','min'];
        var offset = [4, 2, 2, 2, 2];

        var res = [];
        var curr = 0;
        var match = -1;
        for(var i=0;i<labs.length;i++) {
            var x1 = ts1.slice(curr,curr+offset[i]), x2 = ts2.slice(curr,curr+offset[i]);
            if (x1!=x2) {
                match = i;
                break;
            }
            curr+=offset[i];
        }

        if (match==-1) return [];
        return labs.slice(match,labs.length);

    };

    m.timeDiffMinutes = function(ts1, ts2) {
        var millis = m.timestampToUTCDate(ts1).getTime() - m.timestampToUTCDate(ts2).getTime();
        return millis/(1000*60);
    }


    m.timestampToUTCDate = function(ts) {
        return new Date(
            parseInt(ts.slice(0,4)) || 0,
            parseInt(ts.slice(4,6)) || 0,
            parseInt(ts.slice(6,8)) || 0,
            parseInt(ts.slice(8,10)) || 0,
            parseInt(ts.slice(10,12)) || 0
        );
    };


    m.dateToTimestamp = function(d) {
        var utcYear=d.getUTCFullYear(), utcMonth=(d.getUTCMonth()+1), utcDate=d.getUTCDate(), utcHour=d.getUTCHours(), utcMinutes=d.getUTCMinutes();
        return utcYear + twoDigits(utcMonth) + twoDigits(utcDate) + twoDigits(utcHour) + twoDigits(utcMinutes);
    }

    m.shuffleArray = function(array) {
        for (var i = array.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var temp = array[i];
            array[i] = array[j];
            array[j] = temp;
        }
        return array;
    }

    m.parseRef = function(ref) {
        var source = '';
        var searchEngines = ['google', 'yahoo', 'bing'];
        var socialMedia = ['twitter', 't.co', 'facebook'];


        searchEngines.forEach( e => {
            var r = new RegExp();
            r.compile(e, 'g');
            if (ref.match(r)) {
                source = e;
            }
        });

        socialMedia.forEach( y => {
            var r = new RegExp();
            r.compile(y, 'g');
            if (ref.match(r)) {
                source = y;
            }
        });

        return source;
    }

    return m;
}());
