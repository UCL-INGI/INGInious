import web

#Control the session
#There is a little hack to get the sessions to work in debug mode (save in config)
class SessionManager:
	def __init__(self):
		self.session = None
	def init(self, app):
		if web.config.get('_session') is None:
			self.session = web.session.Session(app, web.session.DiskStore('sessions'), {'count': 0})
			web.config._session = self.session
		else:
			self.session = web.config._session
	def get(self):
		return self.session

#From outside of this module, should call sessionManager.get() to get the session.
#SessionManager is init in app.py
sessionManager = SessionManager()