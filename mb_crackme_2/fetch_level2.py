import another

PIN = 9667
filename = 'level2_payload.dll'

# wrap another.fetch_url() so that we can print the url before it's fetched

fetch_url_original = another.fetch_url
def fetch2(x):
    print 'url: ' + x
    return fetch_url_original(x)
another.fetch_url = fetch2


def main():
    key = another.get_url_key(PIN)
    data = another.decode_and_fetch_url(key)
    print 'fetched', len(data), 'bytes'
    decdata = another.get_encoded_data(data)
    with open(filename, 'wb') as f:
        f.write(decdata)
        f.close()
    print 'payload', len(decdata), 'bytes written to', filename

if __name__ == '__main__':
    main()
