#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from __future__ import with_statement
import argparse
import urllib2
import re
import os
import time
import ssl

#压缩内容解压
import gzip
import StringIO
import zlib

HEADERS = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        'Sec-Fetch-User': '?1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        }


PATTERN_TOPIC_PAGING_LIST = r'<span\s+?id="fd_page_top"><div\s+?class="pg">.+?<label>.+?<span\s+?title=".+?(\d+).+?">.+?</span></label><a\s+?href="(.+?-)\d+?\.html".+?</a></div></span>'
PATTERN_PAGING_POSTS_LIST = r'<div\s+?class="c\s+?cl">\s+?<a\s+?href="(.+?\.html)".+?title="(.+?)".+?</a>.+?</div>'
PATTERN_POST_DATE = r'<ignore_js_op>\s+?<img\s+?id="aimg_\d+?".+?zoomfile=".+?/attachment/forum/(20\d{4})/.+?".+?<p><strong>.+?</strong>\s+?<emignore_js_op.+?</div>.+?</ignore_js_op>'
PATTERN_POST_COVER = r'<div\s+?class="imall_lt">\s+?<div\s+?class="ilt"><img\s+?src="(.+/(\w+\.jpg))"></div>\s+?</div>'
PATTERN_POST_IMGS_LIST = r'<ignore_js_op>\s+?<img\s+?id="aimg_\d+?".+?zoomfile="(.+?)".+?<p><strong>(.+?)</strong>\s+?<emignore_js_op.+?</div>.+?</ignore_js_op>'


def unzip(data):
    buf = StringIO.StringIO(data)
    f = gzip.GzipFile(fileobj=buf)
    return f.read()

def decompress(data):
    try:
        return zlib.decompress(data, -zlib.MAX_WBITS)
    except zlib.error:
        return zlib.decompress(data)

def get_html_content(url, timeout=10):
    #超时重试
    try_num = 0
    while try_num < 10:
        try:
            request = urllib2.Request(url, headers=HEADERS)
            response = urllib2.urlopen(request, timeout=timeout)
            content = response.read(1024 * 1024 * 50)
            encoding = response.info().get('Content-Encoding')
        except Exception, e:
            print 'We failed to reach a server: ' + str(e)
            try_num += 1
            print 'try again late 10s, No. ' + str(try_num)
            time.sleep(10)
        else:
            encoding = response.info().get('Content-Encoding')
            if encoding == 'gzip':
                content = unzip(content)
            elif encoding == 'deflate':
                content = decompress(content)
            return content

    print "[Warning] skipping download: " + url
    return None

PATTERN_FORUM_CATEGORY_LIST = r'<div\s+?class="bm\s+?bmw\s+?flg\s+?cl mjbt_\d+?">\s+?<div\s+?class="bm_h\s+?cl">\s+?<span\s+?class="o">.+?</span>\s+?<h2><a\s+?href="([^"]+?)".+?>([^><]+?)</a></h2>\s+?</div>'
def get_categorys_byforum(forum_pair):
    """
    获取论坛下所有分类列表
    """
    forum_url, forum_path = forum_pair

    forum_path = re.sub(r'\s+', '', forum_path)
    if not os.path.exists(forum_path):
        os.makedirs(forum_path)

    html = get_html_content(forum_url)
    if html is None:
        return None

    pattern = re.compile(PATTERN_FORUM_CATEGORY_LIST, re.DOTALL)
    categorys_list = re.findall(pattern, html)
    if categorys_list is None:
        return None

    for category in categorys_list:
        get_topics_bycategory(category, forum_path)


PATTERN_CATEGORY_TOPIC_LIST = r'<tr\s+?class="fl_row">\s+?<td\s+?class="fl_icn".+?<td>\s+?<h2><a\s+?href="([^"]+?)".+?>([^><]+?)</a></h2>.+?</td>.+?<td\s+?class="fl_i">.+?<td\s+?class="fl_by">'
def get_topics_bycategory(category_pair, forum_prefix=None):
    """
    获取分类下所有专区列表
    """
    category_url, category_name = category_pair
    category_path = re.sub(r'\s+', '', category_name)
    if forum_prefix is not None:
        category_path = os.path.join(forum_prefix, category_path)
    if not os.path.exists(category_path):
        os.makedirs(category_path)

    html = get_html_content(category_url)
    if html is None:
        return None

    pattern = re.compile(PATTERN_CATEGORY_TOPIC_LIST, re.DOTALL)
    topic_list = re.findall(pattern, html)
    if topic_list is None:
        return None

    for topic in topic_list:
        get_paging_bytopic(topic, category_path)


def get_paging_bytopic(topic_pair, category_prefix=None):
    """
    获取专区下所有分页列表
    """
    topic_url, topic_name = topic_pair
    topic_path = re.sub(r'\s+', '', topic_name)
    if category_prefix is not None:
        topic_path = os.path.join(category_prefix, topic_path)
    if not os.path.exists(topic_path):
        os.makedirs(topic_path)

    html = get_html_content(topic_url)
    if html is None:
        return None

    pattern = re.compile(PATTERN_TOPIC_PAGING_LIST, re.DOTALL)
    match = re.search(pattern, html)
    if match is None:
        return None

    total_pages, paging_prefix = match.group(1, 2)
    #遍历专区所有分页
    for page_num in range(1, int(total_pages)+1):
        paging_url = paging_prefix + unicode(page_num) + '.html'
        get_posts_bypaging((paging_url, topic_name), topic_path)


def get_posts_bypaging(paging_pair, topic_prefix=None):
    """
    获取分页下所有帖子列表
    """

    paging_url, topic_name = paging_pair
    print u"downloading paging: " + paging_url

    html = get_html_content(paging_url)
    if html is None:
        return None

    pattern = re.compile(PATTERN_PAGING_POSTS_LIST, re.DOTALL)
    post_list = re.findall(pattern, html)
    if post_list is None:
        return None

    for post in post_list:
        get_images_bypost(post, topic_prefix);


def get_images_bypost(post_pair, topic_prefix=None):
    """
    获取帖子内所有图片列表
    """
    post_url, post_name = post_pair

    print u"downloading post: " + post_url

    html = get_html_content(post_url)
    if html is None:
        return None

    html_date = html_cover = html_cnt = html

    #获取相册日期
    pattern_postdate = re.compile(PATTERN_POST_DATE, re.DOTALL)
    match_postdate = re.search(pattern_postdate, html_date)
    if match_postdate is None:
        return None
    post_date = match_postdate.group(1)

    post_path = re.sub(r'\s+', '', post_name)
    if topic_prefix is not None:
        post_path = os.path.join(topic_prefix, post_date, post_path)
    if not os.path.exists(post_path):
        os.makedirs(post_path)

    #下载相册封面图片
    # pattern_cover = re.compile(PATTERN_POST_COVER, re.DOTALL)
    # match_cover = re.search(pattern_cover, html_cover)
    # if match_cover is None:
    #     return None
    # cover_pair = match_cover.group(1, 2)
    # download_image(cover_pair, post_path)


    #下载相册内容图片
    pattern_imgs = re.compile(PATTERN_POST_IMGS_LIST, re.DOTALL)
    #iterator = re.finditer(pattern_imgs, html.read())
    imgs_list = re.findall(pattern_imgs, html_cnt)
    if imgs_list is None:
        return None

    for img in imgs_list:
        download_image(img, post_path)


def download_image(img_pair, post_prefix=None):
    """
    下载图片保存
    """
    img_url, orgin_img_filename = img_pair
    image_filename = os.path.join(post_prefix, orgin_img_filename)

    print "downloading image: " + img_url + " >> " + image_filename + ': ',

    if os.path.exists(image_filename):
        print "<already exist>"
    else:
        image = get_html_content(img_url)
        if image is None:
            print "<download fail>"
            return None

        with open(image_filename, 'wb') as f:
            f.write(image)

        print "<download success>"




if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-type", type=int, default=0, choices=[0, 1, 2, 3, 4]
            , help="""采集类型：
                        0： 整个论坛，(默认);
                        1：分类;
                        2：专区;
                        3：分页;
                        4：帖子;""")
    parser.add_argument("url", help='论坛/分类/专区/分页/帖子的URL')
    parser.add_argument("path", help='论坛/分类/专区/分页/帖子本地存储路径')
    args = parser.parse_args()

    #0： 整个论坛，(默认)；
    if args.type == 0:
        get_categorys_byforum((args.url, args.path))
        pass
    #1：分类;
    elif args.type == 1:
        get_topics_bycategory((args.url, args.path))
        pass
    #2：专区;
    elif args.type == 2:
        get_paging_bytopic((args.url, args.path))
        pass
    #3：分页;
    elif args.type == 3:
        get_posts_bypaging((args.url, args.path))
        pass
    #4：帖子;
    elif args.type == 4:
        get_images_bypost((args.url, args.path))





