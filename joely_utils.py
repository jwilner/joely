import re, random, string

characters = string.uppercase+string.lowercase+string.digits
pw_regex = re.compile('\d')
email_regex = re.compile('^.*@{1}.*\..*^')
url_regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def shorten_dat(url):
    return ''.join(random.choice(characters) for c in url[:len(url)//4 + 1])
