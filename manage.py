from flask_script import Manager
from fanach import app

from fanach.scripts.db import InitDB

if __name__ == "__main__":
	manager = Manager(app)
	manager.add_command("init_db", InitDB())
	manager.run()
	print("データベースを新規作成しました")