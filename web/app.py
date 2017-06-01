from index import app, db
from controllers.sites import Sites
from controllers.green_analytics_script import GreenAnalyticsScript

@app.route('/sites', methods=['GET'])
def sites():
    controller = Sites()
    return controller.respond()

@app.route('/ga-script', methods=['GET'])
def ga_script():
    controller = GreenAnalyticsScript()
    return controller.respond()

@app.route('/', methods=['GET'])
def index():
    return "Hello World!!!"

if __name__ == '__main__':
    app.run()
