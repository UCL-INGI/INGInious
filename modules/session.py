import web

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
sessionManager = SessionManager()