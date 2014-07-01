import web
import modules
import pages

urls = (
    '/', 'pages.index.IndexPage',
    '/index', 'pages.index.IndexPage'
)

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()