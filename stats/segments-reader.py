#!/usr/bin/env python2.7

import sys, getopt
import glob
import string
import operator
import codecs
import robotparser

from urlparse import urlparse
import urllib
import re

def hasLogin(url):
    """
    Detect if a certain URL has a login form
    """

    f = urllib.urlopen(url)
    html = f.read()
    
    pattern_password = r'<[a-z]+.*?(type="password"|name="password").*?>'
    pattern_login = r'<a.*?>(((l|L)og|(s|S)ign) (i|I)n)</a>'
    
    search = re.search(pattern_password, html, re.I)
    if search:
       return True
    
    """
    search = re.search(pattern_login, html, re.I)
    if search:
        return True
    """
    return False


def getSummaryStats(input_dir, output_dir):
    """
    Gets the following statistics by reading the Nutch segments dump:
    - Total Unique Domains
    - # of Pages per Domain
    - # of Images per Domain
    - Domains with robots.txt that Ban Crawling
    - Domains with Login Forms
    """
    
    files = glob.glob(input_dir + '/*/dump')
    total = {}
    images = {}

    total_num = 0
    images_num = 0
    
    robots_banned = 0
    robots_allowed = 0
    
    login_num = 0

    # Keep track of banned domains
    parser = robotparser.RobotFileParser()
    
    banned = []
    login = []
    
    # Use extensions to detect image URLs
    extensions = ['jpeg', 'jpg', 'gif', 'png', 'bmp', 'tif', 'tiff', 'ico']
    
    for f in files:
        print "Checking ... ", f
        fileRead = open(f, 'r')
        for line in fileRead:
            if line.startswith('URL'):
                url = line[line.find('::') + 2:].strip()
                url_parsed = urlparse(url)
                
                domain = url_parsed.netloc
                
                # Read the domain for a robots.txt, if it is first time seeing that domain
                if total.get(domain, 0) == 0:
                    domain_url = url_parsed.scheme + '://' + url_parsed.netloc
                    
                    print domain_url
                    # HTTP errors and robots.txt bans are grouped together
                    try:
                        parser.set_url(domain_url + '/robots.txt')
                        parser.read()
                        
                        if parser.can_fetch('*', domain_url):
                            robots_allowed += 1
                        else:
                            banned.append(domain)
                            robots_banned += 1
                    except:
                        banned.append(domain)
                        robots_banned += 1
                    
                    # Check if the page contains a login form
                    """
                    if hasLogin(domain_url):
                        login_num += 1
                        login.append(domain)
                    """

                total_num += 1
                total[domain] = total.get(domain, 0) + 1
                
                site_list = url_parsed.path.split('.')
                if site_list[-1] in extensions:
                    images_num += 1
                    images[domain] = images.get(domain, 0) + 1
        fileRead.close()
    
    print "Total: ", total_num
    print "Images: ", images_num
    print "Total Domains: ", len(total)
    print
    print "Robots Allowed: ", robots_allowed
    print "Robots Banned: ", robots_banned
    
    # Write to output files
    errors = 0
    
    with codecs.open(output_dir + '/total.txt', 'w', 'utf-8') as o:
        sorted_total = sorted(total.items(), key=operator.itemgetter(1), reverse=True)
        for host, count in sorted_total:
            host = host.decode('utf-8')
            try:
                o.write('%s, %d\n' %(host, count))
            except:
                errors += 1

    with codecs.open(output_dir + '/images.txt', 'w', 'utf-8') as o:
        sorted_images = sorted(images.items(), key=operator.itemgetter(1), reverse=True)
        for host, count in sorted_images:
            host = host.decode('utf-8')
            try:
                o.write('%s, %d\n' %(host, count))
            except:
                continue
    
    with codecs.open(output_dir + '/banned.txt', 'w', 'utf-8') as o:
        for host in banned:
            host = host.decode('utf-9')
            try:
                o.write('%s, %d\n' % host)
            except:
                continue

    print "Error Domains: ", errors


def main(argv=sys.argv):
    usage = "seugment-reader.py -i <input_dir> -o <output_dir>"
    input = ""
    output = ""
    try:
        opts, args = getopt.getopt(argv, "hi:o:")
    except getopt.GetoptError:
        print usage
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print usage
            sys.exit(2)
        elif opt == '-i':
            input = arg
        elif opt == '-o':
            output = arg

    getSummaryStats(input, output)


if __name__ == '__main__':
    main(sys.argv[1:])