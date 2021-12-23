import mosspy
import sys
import getopt
import glob

userId = 120445038

m = mosspy.Moss(userId, 'python')
m.setCommentString("Moss is working")
#m.addBaseFile("genmihatests.py")

def get_report(directory):
    files = glob.glob(directory + '/*.py')

    for file in files:
        m.addFile(file)

    url = m.send(lambda file_path, display_name: print('*', end='', flush=True))

    print("Report is saved under ./report/report.html")
    print(url)

    m.saveWebPage(url, "report/report.html")

    mosspy.download_report(url, "report/report", connections=8, log_level=10, on_read=lambda url: print('*', end='', flush=True) )


def main(argv):
    directoryToTest = ""

    try:
        opts, args = getopt.getopt(argv, 'd:u')
    except getopt.GetoptError:
        print('python3 plagiat_checker -d <directory_to_check>')

    for opt, arg in opts:
        if opt == '-d':
            print(arg)
            get_report(arg)


if __name__ == "__main__":
    main(sys.argv[1:])
