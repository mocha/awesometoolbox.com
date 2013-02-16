import urllib2

def url_exists(url):
	try:
	    urllib2.urlopen(url)
	    return True         # URL Exist
	except ValueError, ex:
	    return False        # URL not well formatted
	except urllib2.URLError, ex:
	    return False        # URL don't seem to be alive