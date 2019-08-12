# -*- coding: utf-8 -*-

import urllib2, json, ftfy, re, string, time, datetime
from collections import defaultdict
from dateutil.parser import parse as parse_dt
from lxml import html
from scraper_data import SOURCE_RULES, STORIES

DEBUG = False

def process_story(source, url, date, metadata):
    '''
    Opens the URL and scrapes the relevant text as per the rules in SOURCE_RULES.
    Returns a dict w/ the headline and story content (plus passed-through date/metadata) if it worked; otherwise returns None.
    Also computes a simplistic regex-based word-count as a quality check to compare with GDELT wordcount, plus some other quality warnings.
    '''
    noncritical_warnings = {}
    # initial sanity check on URL embedded date code
    url_date_code = re.search(r'/\d{4}/(\d{2}|\w{3})/(\d{1,2}/)?',url)
    if url_date_code:
        url_date_code = parse_dt(url_date_code.group(0), ignoretz=True)
        gkg_date_code = datetime.datetime.strptime(date,'%Y%m%d%H%M%S')
        diff = gkg_date_code - url_date_code
        if abs(diff.days) > 31:
            print '+'*20
            print 'WARNING: Date-code embedded in URL differs from date-code provided by GKG by {} days! URL-implied date is {}. Skipping {}.'.format(diff.days,url_date_code,url)
            print '+'*20
            return None

    # wait a bit to avoid getting blocked 
    time.sleep(2)
    # open the URL and read the data
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    opener.addheaders = [('User-Agent', 'news scraper for mona project')]
    try:
        # wrap file obj in ftfy.fix_file() to organize unicode
        content = ''.join([x for x in ftfy.fix_file(opener.open(url))])
    except urllib2.HTTPError as e:
        print '+'*20
        print 'WARNING: HTTP error for "{}": {} - {}. Skipping.'.format(url, e.code, e.reason)
        print '+'*20
        return None
    except urllib2.URLError as e:
        print '+'*20
        print 'WARNING: URL error for "{}": {}. Skipping.'.format(url, e.reason)
        print '+'*20
        return None
    except Exception as e: 
        print '+'*20
        print 'WARNING: Unexpected exception for "{}": {}. Skipping.'.format(url, e.message)
        print '+'*20
        return None
    
    # parse the HTML tree
    try:
        tree = html.fromstring(content)
    except Exception:
        print '+'*20
        print 'WARNING: lxml was unable to parse HTML tree for "{}". Skipping.'.format(url)
        print '+'*20
        return None
        
    # translate <br> to \n
    for br in tree.xpath('*//br'):
        br.tail = '\n\n' + br.tail if br.tail else '\n\n'
    
    # apply source-specific preprocessing to the tree
    if SOURCE_RULES[source].get('tree_preprocessor'):
        tree = SOURCE_RULES[source]['tree_preprocessor'](tree)

    # if we didn't figure out the pub date earlier, do it now
    if not url_date_code and not SOURCE_RULES[source].get('timestamp_xpath'):
        print '*'*20
        print 'No date code in URL and no timestamp xpath rule defined! Skipping {}'.format(url)
        print '*'*20
        return None
    elif not url_date_code and SOURCE_RULES[source].get('timestamp_xpath'): 
        article_date_els = tree.xpath(SOURCE_RULES[source]['timestamp_xpath'])
        article_date_string = ' '.join([e.text_content() for e in article_date_els])
        if not article_date_string.strip():
            print '+'*20
            print 'WARNING: No publication date could be found! Skipping {}.'.format(url)
            print '+'*20
            return None
        try:
            article_date = parse_dt(article_date_string, fuzzy=True, ignoretz=True)
        except:
            print '+'*20
            print 'WARNING: Unable to evaluate article publication date! No sanity check possible. Skipping {}.'.format(url)
            print '+'*20
            return None
        gkg_date_code = datetime.datetime.strptime(date,'%Y%m%d%H%M%S')
        diff = gkg_date_code - article_date
        if abs(diff.days) > 31:
            print '+'*20
            print 'WARNING: Date-code embedded in article differs from date-code provided by GKG by {} days! Article date is {}. Skipping {}.'.format(diff.days,article_date,url)
            print '+'*20
            return None

    # read headline using xpath
    # if necs, adapt to any known-naughty URLs which require special rules
    if SOURCE_RULES[source].get('naughty_list',{}).get(url,{}).get('headline_xpath',{}):
        headline_xpath = SOURCE_RULES[source]['naughty_list'][url]['headline_xpath'] 
    else:
        headline_xpath = SOURCE_RULES[source]['headline_xpath']
    if headline_xpath:
        headline = '\n\n'.join([e.text_content().lstrip() for e in tree.xpath(headline_xpath)])
    else:
        print 'No headline rule defined for source "{}", skipping "{}"'.format(source,url)
        return None
    if DEBUG:
        print '*'*20
        print url
        print '-'*20
        print headline

    # read story content using xpath
    # if necs, adapt to any known-naughty URLs which require special rules
    if SOURCE_RULES[source].get('naughty_list',{}).get(url,{}).get('content_xpath',{}):
        content_xpath = SOURCE_RULES[source]['naughty_list'][url]['content_xpath'] 
    else:
        content_xpath = SOURCE_RULES[source]['content_xpath']
    
    # clean up whitespace by replacing all tabs or spaces (incl the nbsp, \xa0) from the text with a single space
    if content_xpath:
        text_blocks = [re.sub(r'[\t\xa0 ]+', ' ', e.text_content()) for e in tree.xpath(content_xpath)]
    else:
        print 'No content rule defined for source "{}", skipping "{}"'.format(source,url)
        return None
    story_content = '\n\n'.join(text_blocks)
    if DEBUG:
        print '-'*20
        print story_content
        print '*'*20

    # find repetitive blocks of text and add warning if necs
    rep_count = len([t for t in text_blocks if t.strip()]) - len(set([t for t in text_blocks if t.strip()]))
    if rep_count:
        noncritical_warnings['repetitive_text_block_count'] = rep_count
        if DEBUG:
            print '^'*20
            print 'NONCRITICAL: {} repetitive text blocks were found! Very suspicious, consider filtering {}.'.format(rep_count,url)
            print '^'*20
              
    # exclude any data with empty headline or empty story_content
    if not headline or not story_content:
        print '+'*20
        print 'WARNING: Headline or story from "{}" was blank; excluding from output.'.format(url)
        print '+'*20
        return None
    
    # copy the metadata
    try:
        metadict = eval(metadata)
        assert type(metadict) is dict
    except AssertionError as e:
        print '+'*20
        print 'WARNING: Metadata string "{}" does not evaluate to a dict. Skipping "{}".'.format(metadata, url)
        print '+'*20
        return None
    except Exception as e:
        print '+'*20
        print 'WARNING: Unexpected error evaluating metadata "{}". Skipping "{}".'.format(metadata, url)
        print '+'*20
        return None
            
    # some additional sanity checking for character encoding
    strangechars = defaultdict(list)
    for i, c in enumerate(headline+story_content):
        if '\\x' in repr(c) or '\\00' in repr(c):
            strangechars[c].append(i)
    if strangechars:
        strangechars = dict(strangechars)
        noncritical_warnings['suspicious_characters'] = strangechars
        if DEBUG:
            print '^'*20            
            print 'NONCRITICAL: Found potentially-suspicous characters: {} ("{}")'.format(strangechars, url)
            print '^'*20
        
    # regex wordcount as a sanity check vs. gdelt wordcount (black box)
    regex_wordcount = len(re.findall(r'\w+', ''.join([c for c in story_content if c not in string.punctuation])))
    if not metadict.get('wordcount'):
        noncritical_warnings['wordcount_mismatch'] = {'gdelt':None, 'scraper_regex':regex_wordcount} 
        if DEBUG:
            print '^'*20
            print 'NONCRITICAL: Metadata missing value for "wordcount" so no sanity-check possible. ({})'.format(url)
            print '^'*20
    elif abs(regex_wordcount - metadict['wordcount'])/float(metadict['wordcount']) > 0.05:
        noncritical_warnings['wordcount_mismatch'] = {'gdelt':metadict['wordcount'], 'scraper_regex':regex_wordcount} 
        if DEBUG:
            print '^'*20
            print 'NONCRITICAL: GDELT reports {} words but scraped content contains approximately {} ({})'.format(metadict['wordcount'], regex_wordcount, url)
            print '^'*20
    
    # if we've made it this far w/o returning None, everything's good to go
    return {'headline':headline, 'story_content':story_content, 'date':date, 'metadata':metadict, 'wordcount_as_scraped':regex_wordcount, 'warnings':noncritical_warnings}
        
if __name__ == '__main__':   
    # call process_story for all stories and save the result in JSON format
    output = {s[1]:process_story(*s) for s in STORIES}
    skip_count = len([v for v in output.values() if not v])
    with open('scraped_articles.json', 'wb') as outfile:
        output = {k:v for k, v in output.items() if v}
        json.dump(output, outfile)
        print '='*20
        print 'Finished! Output for {} URLs written to file "{}"'.format(len(output),outfile.name)
        print 'Skipped a total of {} URLs for various reasons; see stdout.'.format(skip_count)
        print 'Logged a total of {} noncritical warnings.'.format(sum([len(v['warnings']) for v in output.values() if v.get('warnings')]))
        print '='*20
        
