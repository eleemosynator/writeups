import another

for i in xrange(1000000):
    key = another.get_url_key(i)
    if another.check_key(key):
        print 'PIN: ', i
        print 'key: ', key
        break
