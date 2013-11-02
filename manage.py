from flask.ext.script import Manager
from joely import db,app

manager = Manager(app)

@manager.command
def init():
    db.drop_all()
    db.create_all()

if __name__ == "__main__":
    manager.run()
