from index import app, db
from controllers.sites import Sites

@app.route('/sites', methods=['GET', 'POST'])
def sites():
    controller = Sites()
    return controller.respond()

@app.route('/', methods=['GET'])
def index():
    return "Hello World!!!"

if __name__ == '__main__':
    app.run()
