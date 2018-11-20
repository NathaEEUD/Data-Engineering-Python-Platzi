import argparse
import datetime
import csv
import logging
logging.basicConfig(level=logging.INFO)
import re

from requests.exceptions import HTTPError
from urllib3.exceptions import MaxRetryError 

import news_page_objects as news
from common import config

logger = logging.getLogger(__name__)
is_well_formed_link = re.compile(r'^https?://.+/.+$') # http://example.com/hello
is_root_path = re.compile(r'^/.+$') # /some-text

def _news_scraper(news_site_uid):
    host = config()['news_sites'][news_site_uid]['url']

    logging.info('Beginning scraper for {}'.format(host))
    homepage = news.HomePage(news_site_uid, host)

    articles = []
    ud_programs = []

    if news_site_uid == 'udistrital':
        for info in homepage.udistrital_info:
            ud_info_programs = news.UdProgramsPage(news_site_uid, info)

            if ud_info_programs:
                logger.info('Info fetched!')
                ud_programs.append(ud_info_programs)
                # break

            _save_ud_programs(news_site_uid, ud_programs)
    else:
        for link in homepage.article_links:
            article = _fetch_article(news_site_uid, host, link)

            if article:
                logger.info('Article fetched!')
                articles.append(article)
                break

        _save_articles(news_site_uid, articles)

def _save_ud_programs(news_site_uid, ud_programs):
    now = datetime.datetime.now().strftime('%Y_%m_%d')
    out_file_name = '{news_site_uid}_{datetime}_ud_programs.csv'.format(
        news_site_uid=news_site_uid,
        datetime=now)

    csv_headers = list(filter(lambda property: not property.startswith('_'), dir(ud_programs[0])))

    with open(out_file_name, mode='w+') as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)

        for info_program in ud_programs:
            row = [str(getattr(info_program, prop)) for prop in csv_headers]
            writer.writerow(row)

def _save_articles(news_site_uid, articles):
    now = datetime.datetime.now().strftime('%Y_%m_%d')
    out_file_name = '{news_site_uid}_{datetime}_articles.csv'.format(
        news_site_uid=news_site_uid,
        datetime=now)

    csv_headers = list(filter(lambda property: not property.startswith('_'), dir(articles[0])))

    with open(out_file_name, mode='w+') as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)

        for article in articles:
            row = [str(getattr(article, prop)) for prop in csv_headers]
            writer.writerow(row)

def _fetch_article(news_site_uid, host, link):
    logger.info('Start fetching article at {}'.format(link))

    article = None
    try:
        article = news.ArticlePage(news_site_uid, _build_link(host, link))
    except (HTTPError, MaxRetryError) as e:
        logger.warning('Error while fetching the article', exc_info=False)

    if article and not article.body:
        logger.warning('Invalid article. There is no body')
        return None

    return article

def _build_link(host, link):
    if is_well_formed_link.match(link):
        return link
    elif is_root_path.match(link):
        return '{}{}'.format(host, link)
    else:
        return '{host}/{uri}'.format(host=host, uri=link)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    news_site_choices = list(config()['news_sites'].keys())
    parser.add_argument('news_site',
                        help='The news site that you want to scrape',
			type=str,
			choices=news_site_choices)

    args = parser.parse_args()
    _news_scraper(args.news_site)
