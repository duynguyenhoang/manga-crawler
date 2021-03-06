#!/usr/bin/python

from __main__ import print_info
from abc import ABCMeta, abstractmethod
import os
import zipfile


class Crawler(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, url):
        pass

    @abstractmethod
    def chapter_info(self, chapter_data):
        pass

    @abstractmethod
    def download_chapter(self, chapter, download_directory, download_name):
        pass

    @abstractmethod
    def series_chapters(self):
        pass

    @abstractmethod
    def series_info(self, search):
        pass

    @staticmethod
    def zip_files(files, filename):
        zipf = zipfile.ZipFile(filename, mode="w")
        for f in files:
            zipf.write(f, os.path.basename(f))
            os.remove(f)
        print_info("Zip created: " + filename.replace(os.environ['HOME'], "~"))

    def default_user_agent(self):
        """Get default user agent to whole project"""
        return 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)' \
               ' Chrome/32.0.1667.0 Safari/537.36'
