# /usr/bin/python3.5

from __main__ import print_info
from bs4 import BeautifulSoup
from Scrapers.Crawler import Crawler
import gzip
import io
import logging
import re
import urllib.request, urllib.error, urllib.parse
from functools import cmp_to_key


class TruyenTranhTuan(Crawler):
    site_name = 'TruyenTranhTuan'
    uses_groups = False

    def __init__(self, url):
        self.url = url
        super(TruyenTranhTuan, self).__init__(url)
        match_chapter = re.match(r'(.+)truyentranhtuan\.com\/(.+)-chuong-(\d+)', url, flags=re.IGNORECASE)
        if match_chapter:
            self.chapter_number = match_chapter.group(3)
            self.page = BeautifulSoup(self.open_url(self.chapter_series(url)), "html.parser")
            self.init_with_chapter = True
            logging.debug('Object initialized with chapter')
        else:
            self.page = BeautifulSoup(self.open_url(url), "html.parser")
            self.init_with_chapter = False
            self.chapter_number = 0
            logging.debug('Object initialized with series')
        logging.debug('Object created with ' + url)

    def chapter_series(self, url):
        """Returns the series page for an individual chapter URL.
        Useful for scraping series metadata for an individual chapter"""
        return url

    # Returns a dictionary containing chapter number, chapter name and chapter URL.
    def chapter_info(self, chapter_data):
        logging.debug('Fetching chapter info')
        chapter_url = str(chapter_data['href'])

        chapter_number = re.search(r'(\w+)-chuong-(\w+)', chapter_url, flags=re.IGNORECASE).group(2)

        logging.debug('Manga Name: {}'.format(self.series_info('title')))
        logging.debug('Chapter number: {}'.format(chapter_number))
        logging.debug('Chapter name: ' + str(chapter_data.text))
        logging.debug('Chapter URL: ' + chapter_url)

        return {"chapter": chapter_number, "name": chapter_data.text, "url": chapter_url}

    # Returns the image URL for the page.
    def chapter_images(self, chapter_url):
        logging.debug('Fetching chapter images')
        image_list = []

        page = BeautifulSoup(self.open_url(chapter_url.encode('ascii', 'ignore').decode('utf-8')), "html.parser")
        scripts = page.find("div", {"id": "containerRoot"}).find_all('script')
        for script in scripts:
            if re.search(r'lstImages', script.text):
                for match in re.findall(r'lstImages\.push\(".*"\);', script.text):
                    image_list.append(re.search(r'lstImages\.push\("(.*)"\);', match).group(1))
                break

        logging.debug('Chapter images: ' + str(image_list))
        return image_list

    def download_chapter(self, chapter, download_directory, download_name):
        files = []
        warnings = []
        logging.debug('\n************************************************')
        logging.debug('Downloading chapter {}.'.format(chapter["url"]))
        page = BeautifulSoup(self.open_url(chapter["url"].encode('ascii', 'ignore').decode('utf-8')), "html.parser")
        scripts = page.find_all('script')
        # TODO
        chapter_name = chapter["url"].strip('/').split('/')
        chapter_name = chapter_name[len(chapter_name) - 1]
        image_name = 1
        for script in scripts:
            if re.search(r'(var slides_page_path = \[")(.+)("\];)', script.text):
                image_url = re.search(r'(var slides_page_path = \[")(.+)("\];)', script.text).group(2)
                need_short = 1
            elif re.search(r'(var slides_page_url_path = \[")(.+)("\];)', script.text):
                image_url = re.search(r'(var slides_page_url_path = \[")(.+)("\];)', script.text).group(2)
                need_short = 0
            else:
                continue

            image_urls = image_url.split('","')
            if need_short == 1:
                image_urls = sorted(image_urls, key=cmp_to_key(cmp_items))

            for image_url in image_urls:
                if image_url == '':
                    continue

                file_extension = re.search(r'.*\.([A-Za-z]*)', image_url).group(1)
                logging.debug('Downloading image ' + image_url)
                req = urllib.request.Request(image_url, headers={
                    'User-agent': self.default_user_agent(),
                    'Accept-encoding': 'gzip'})
                try:
                    response = urllib.request.urlopen(req)
                except urllib.error.HTTPError as e:
                    print_info('WARNING: Unable to download file ({}).'.format(str(e)))
                    warnings.append(
                        'Download of page {}, chapter {:g}, series "{}" failed.'.format(image_name, chapter["chapter"],
                                                                                        self.series_info('title')))
                    continue
                filename = '{}/{}-{:06d}.{}'.format(download_directory, chapter_name, image_name, file_extension)
                f = open(filename, 'wb')
                f.write(response.read())
                f.close()
                logging.debug('Saved image ' + filename)
                files.append(filename)
                image_name += 1
            break

        filename = download_directory + '/' + download_name
        self.zip_files(files, filename)
        logging.debug('Finished {} Chapter'.format(chapter_name))

        return warnings

    # Function designed to create a request object with correct headers, open the URL and decompress it if it's gzipped.
    def open_url(self, url):
        logging.debug("Opening URL: " + url)
        headers = {
            'User-agent': self.default_user_agent(),
            'Accept-encoding': 'gzip', 'Cookie': 'vns_Adult=yes'}
        req = urllib.request.Request(url, headers=headers)
        response = urllib.request.urlopen(req)

        if response.info().get('Content-Encoding') == 'gzip':
            buf = io.BytesIO(response.read())
            data = gzip.GzipFile(fileobj=buf, mode="rb")
            return data
        else:
            return response.read()

    def series_chapters(self):
        chapters = []
        if self.init_with_chapter:
            logging.debug('Fetching single chapters')
            chapters.append(
                {"chapter": self.chapter_number, "name": "Chapter " + str(self.chapter_number), "url": self.url}
            )
        else:
            # If the object was initialized with a chapter, only return the chapters.
            logging.debug('Fetching series chapters')
            chapter_row = self.page.find("div", {"id": "manga-chapter"}).find_all("span", {"class": "chapter-name"})

            for chapter in chapter_row:
                chapters.append(self.chapter_info(chapter.find("a")))

        return chapters[::-1]

    def series_info(self, search):
        def title():
            if not self.init_with_chapter:
                return self.page.find("h1", {"itemprop": "name"}).text.strip()
            else:
                return self.page.find("a", {"class": "mangaName"}).text.strip()

        def description():
            if not self.init_with_chapter:
                return self.page.find("div", {"id": "manga-summary"}).find("p").text.strip('\n')
            else:
                # @todo Get for specific chapter
                return ""

        def author():
            return self.page.select('a[href*="/danh-sach-truyen/"]')[0].text.title()

        options = {"title": title, "description": description, "author": author}
        return options[search]()


def cmp_items(a, b):
    image_index_a = re.search(r'.*-([0-9]*)\.([A-Za-z]*)', a).group(1)
    image_index_a = int(image_index_a)
    image_index_b = re.search(r'.*-([0-9]*)\.([A-Za-z]*)', b).group(1)
    image_index_b = int(image_index_b)
    if image_index_a > image_index_b:
        return 1
    elif image_index_a == image_index_b:
        return 0
    else:
        return -1
