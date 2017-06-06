from flask import request, render_template
from models.message import Message
from models.site import Site
from index import db, app
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker, scoped_session
from operator import itemgetter
import json

def get_response_string(data):
    obj = {
        'data': data,
        'sum': sum(map(itemgetter(1), data))
    }
    return json.dumps(obj)


def get_option(value, allowed, default):
    if value in allowed:
        return value
    else:
        return default


class MetricData():

    Session = scoped_session(sessionmaker(bind=db.engine))

    def respond(self):
        metric = request.args['name']
        metric_fn = getattr(self, 'report_' + metric, None)
        if callable(metric_fn):
            return get_response_string(metric_fn(request.args))
        return get_response_string([])

    def report_uv_all(self, args):
        return self.messages_per_interval(args.get('token'), message_type='new_all', interval_size='day')

    def report_uv_month(self, args):
        return self.messages_per_interval(args.get('token'), message_type='new_month', interval_size='day')

    def report_uv_day(self, args):
        return self.messages_per_interval(args.get('token'), message_type='new_day', interval_size='day')

    def report_page_load(self, args):
        return self.messages_per_interval(args.get('token'), message_type='page_load', interval_size='day')

    def report_site_uv(self, args):
        group_by = get_option(args.get('group_by'), set(['minute', 'hour', 'day', 'month', 'year']), 'day')
        domain = args.get('domain')
        return self.messages_per_interval(args.get('token'),
            message_type='site_visit_by_{}'.format(group_by),
            interval_size=group_by,
            domain=domain)

    def report_site_visits(self, args):
        group_by = get_option(args.get('group_by'), set(['minute', 'hour', 'day', 'month', 'year']), 'day')
        domain = args.get('domain')
        return self.messages_per_interval(args.get('token'),
            message_type='site_load',
            interval_size=group_by,
            domain=domain)

    def report_domains(self, args):
        return self.get_site_hostnames(args.get('token'))

    def messages_per_interval(self, token, message_type,
            interval_size='day',
            domain=None):
        s = self.Session()

        since = datetime.utcnow() - timedelta(30)
        until = datetime.utcnow()
        options = {
            'site_key': token,
            'msg_type': message_type,
            'since': since,
            'until': until,
            'interval_size': interval_size,
            'domain': domain,
        }

        filters = [
            "site_id = (SELECT site_id FROM sites WHERE site_key = :site_key)",
            "message->>'type' = :msg_type",
            "ts >= :since",
            "ts < :until"
        ]

        if domain is not None:
            filters.append("message->>'p' LIKE :domain")

        query = '''
            SELECT extract(epoch from day) as ts, COUNT(*) AS uniques
            FROM (SELECT date_trunc(:interval_size, ts) AS day
                FROM messages
                WHERE {}) uniques
            GROUP BY day
            ORDER BY day ASC
        '''.format(' AND '.join(filters))

        grouped_counts = s.execute(query, options).fetchall()

        return [[int(ts), count] for ts, count in grouped_counts]

    def get_site_hostnames(self, token):
        since = datetime.utcnow() - timedelta(30)
        until = datetime.utcnow()
        s = self.Session()
        options = {
            'site_key': token,
            'since': since.strftime("%Y%m%d %H:%M"),
            'until': until.strftime("%Y%m%d %H:%M"),
        }
        hostnames = s.execute('''SELECT message->>'p' AS hostname, count(*) AS pages
            FROM messages
            WHERE site_id = (SELECT site_id FROM sites WHERE site_key = :site_key)
                AND message->>'type' = 'site_load'
                AND ts >= :since
                AND ts < :until
            GROUP BY message->>'p'
        ''', options).fetchall()

        return filter(lambda h: ';' not in h[0], map(list, hostnames))
