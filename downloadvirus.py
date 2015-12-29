#-*- coding: utf-8 -*-
#!/usr/bin/env python
import os
import sys
import urllib2
import urlparse
import re
import zlib
import subprocess
import time
#import msvcrt
#import socks
#import socket
#import pdb

reload(sys)
sys.setdefaultencoding('utf8')


class GatherFileList:
    def __init__(self, baseurl, headers):
        self.baseurl = baseurl
        self.headers = headers

    def gatherfilelist(self):
        try:
            #socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 6999)
            #socket.socket = socks.socksocket

            req = urllib2.Request(self.baseurl, headers = self.headers)
            res = urllib2.urlopen(req, timeout = 3)
            #pdb.set_trace()
            pagedata = res.read().decode('utf-16')
            #pagedata = res.read().decode('utf-16-le').encode('utf-8')
            if res.info().get("Content-Encoding") == "gzip":
                pagedata = zlib.decompress(pagedata, 16 + zlib.MAX_WBITS)

        except urllib2.URLError, e:
            if hasattr(e, "code"):
                print e.code
                if hasattr(e, "reason"):
                    print e.reason

        #pdb.set_trace()
        patternstr = r'<A.*?href="(.*?)"><B>'
        pattern = re.compile(patternstr, re.I|re.S)
        items = re.findall(pattern, pagedata)
        #print items
        #pdb.set_trace()
        if not items:
            print 'gather virus file list failed!'
            return None

        return items

class DownloadFile:
    def __init__(self, directory):
        self.directory = directory

    def downloadfile(self, remotefile):
        try:
            fileurl = urllib2.urlopen(remotefile, timeout = 3)

            scheme, netloc, path, query, fragment = urlparse.urlsplit(remotefile)
            filename = os.path.basename(path)
            if not filename:
                filename = 'downloaded.file'

            absfilename = os.path.join(self.directory, filename)
            with open(absfilename, 'wb') as f:
                meta = fileurl.info()
                meta_func = meta.getheaders if hasattr(meta, 'getheaders') else meta.get_all
                meta_length = meta_func("Content-Length")
                file_size = None
                if meta_length:
                    file_size = int(meta_length[0])

                print "Downloading: %s Bytes: %s" % (filename, file_size)
                file_size_dl = 0
                block_sz = 8192
                while True:
                    buffer = fileurl.read(block_sz)
                    if not buffer:
                        break

                    file_size_dl += len(buffer)
                    f.write(buffer)

                    status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
                    status = status + chr(8)*(len(status)+1)
                    print status,

        except urllib2.URLError, e:
            if hasattr(e, "reason"):
                print str(e.reason) + ': ' + remotefile


if __name__ == '__main__':
    argc = len(sys.argv)
    if argc != 2 and argc != 3:
        print '%s url [file]' % sys.argv[0]
        exit(0)

    #virus_url = 'http://localhost:8000/'
    virus_url = sys.argv[1]
    headers = {
        'Host':'', 'Connection':'keep-alive',
        'Cache-Control':'max-age=0', 'Accept': 'text/html, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (X11;Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.89 Safari/537.36',
        'DNT':'1', 'Referer':
        '', 'Accept-Encoding': 'gzip, deflate,sdch', 'Accept-Language': 'zh-CN,zh;q=0.8,ja;q=0.6'
    }


    virusdir = os.getcwd() + '/' + 'virus'
    if not os.path.exists(virusdir):
        os.mkdir(virusdir)

    gc = GatherFileList(virus_url, headers)
    filelist = gc.gatherfilelist()

    dw = DownloadFile(virusdir)
    if argc == 3:
        for remotefile in filelist:
            specfile = os.path.basename(remotefile)
            if 0 == cmp(specfile, sys.argv[2]):
                dw.downloadfile(remotefile)
                break
    else:
        for remotefile in filelist:
            dw.downloadfile(remotefile)
            #raw_input("continue downloading?")
            #msvcrt.getch()


