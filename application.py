import os
from flask import Flask
from model import db

#----------------------------------------
# initialization
#----------------------------------------

application = Flask(__name__)  # Amazon Beanstalk bs
app = application              # ...and a hack around it

app.config.update(
    DEBUG = True,
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://ebroot:instaquote@aa1ame3lqpnmuv0.clozqiwggjtt.us-east-1.rds.amazonaws.com/echo_webapp'

db.init_app(app)

#----------------------------------------
# controllers
#----------------------------------------

@app.route("/")
def hello():
    return "Hello from Python!"



#----------------------------------------
# launch
#----------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
