from index import app, db
from controllers.sites import Sites
from controllers.messages import Messages
from controllers.green_analytics_script import GreenAnalyticsScript
from controllers.analyze import Analyze
from controllers.metric_detail import MetricData
import json

@app.route('/sites', methods=['GET'])
def sites():
    controller = Sites()
    return controller.respond()

@app.route('/ga-script', methods=['GET'])
def ga_script():
    controller = GreenAnalyticsScript()
    return controller.respond()

@app.route('/collect', methods=['GET', 'POST'])
def collect():
    controller = Messages()
    return controller.respond()


@app.route('/', methods=['GET'])
def index():
    return "Hello World!!!"

@app.route('/sample-dashboard', methods=['GET'])
def testDashboard():
    controller = Analyze()
    return controller.respond()


@app.route('/metric_details', methods=['GET'])
def testMetric():
    controller = MetricData()
    return controller.respond()

if __name__ == '__main__':
    app.run(debug=True)
