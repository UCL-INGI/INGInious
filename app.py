import web
import modules
import pages
from modules.session import sessionManager

urls = (
    '/', 'pages.index.IndexPage',
    '/index', 'pages.index.IndexPage',
    '/course/([^/]+)', 'pages.course.CoursePage'
)

app = web.application(urls, globals())
sessionManager.init(app)

if __name__ == "__main__":
    app.run()