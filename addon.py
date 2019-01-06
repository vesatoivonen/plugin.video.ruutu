# -*- coding: utf-8 -*-
import urllib2
import re
import xml.etree.ElementTree as ET
import json
import time
import resources.lib.xbmcutil as xbmcUtil
import sys

reload(sys)
sys.setdefaultencoding('utf8')

def request(url, as_json=False):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    try:
        response = urllib2.urlopen(req)
        content = response.read()
        response.close()
        if as_json:
            return json.loads(content)
        return content
    except urllib2.HTTPError:
        return []


class RuutuAddon(xbmcUtil.ViewAddonAbstract):
    ADDON_ID = 'plugin.video.ruutu'

    def __init__(self):
        xbmcUtil.ViewAddonAbstract.__init__(self)
        self.NEXT = '>>> %s >>>' % self.lang(33078)
        self.PAGESIZE = 15

        self.addHandler(None, self.handleMain)
        self.addHandler('grid', self.listGrid)
        self.addHandler('seasons', self.listSeasons)
        self.addHandler('season', self.listSeason)
        self.addHandler('search', self.handleSearch)

    def getSeasonLink(self, seasonId):
        url = "https://prod-component-api.nm-services.nelonenmedia.fi/api/component/26004?limit={limit}&current_season_id={sid}"
        return url.format(limit=self.PAGESIZE, sid=seasonId)

    def getSeasons(self, seriesUrl):
        content = request(seriesUrl)
        ret = []
        rgx = r"&quot;href&quot;:&quot;/grid/(\d+)&quot;,&quot;label&quot;:&quot;([^&]+?)&quot;"
        for sid, title in re.findall(rgx, content):
            if 'saattaisi kiinnostaa' in title:
                continue
            ret.append({'link': self.getSeasonLink(sid), 'title': title})
        return ret

    def addGrid(self, name, gid, page=1):
        self.addViewLink(name, 'grid', page, {'gid': gid})

    def handleMain(self, page, args):
        self.addViewLink(self.lang(30021), 'search', 1, {})

        self.addGrid("Katsotuimmat", 678)
        self.addGrid("Kotimainen viihde", 679)
        self.addGrid("Kotimainen reality", 733)
        self.addGrid("Elokuvat", 238)
        self.addGrid("Ruutu alkuperäissarjat", 5333)
        self.addGrid("Dokumentit", 732)
        self.addGrid("Jännitys ja draama", 533)
        self.addGrid("Lifestyle", 602)
        self.addGrid("Kansainvälinen reality ja viihde", 603)
        self.addGrid("Cirkus - brittidraama", 6010)

        self.addGrid("Lasten katsotuimmat", 319)
        self.addGrid("Lasten uusimmat", 398)
        self.addGrid("Lasten ruutu suosittelee", 320)
        self.addGrid("Legot", 391)
        self.addGrid("Hulvatonta hauskanpitoa", 392)
        self.addGrid("Seikkailuja", 393)
        self.addGrid("Tyttöenergiaa", 394)
        self.addGrid("Sankarit", 395)
        self.addGrid("Eläinystäviä", 396)
        self.addGrid("Perheen pienimmille", 397)
        self.addGrid("Lasten elokuvat", 584)

    def handleSearch(self, page, args):
        url = 'https://prod-component-api.nm-services.nelonenmedia.fi/api/component/337?offset={offset}&limit={limit}&search_term={query}'

        if 'query' not in args:
            keyboard = xbmc.Keyboard()
            keyboard.setHeading(self.lang(30080))
            keyboard.doModal()
            if (keyboard.isConfirmed() and keyboard.getText() != ''):
                query = keyboard.getText()
                args['query'] = query

        url = url.format(offset=(page - 1) * self.PAGESIZE,
                         limit=self.PAGESIZE,
                         query=args['query'])
        items = request(url, as_json=True).get('items', [])
        for episode in items:
            video_id = str(episode['link']['target']['value'])
            label = "{} - {}".format(episode['footer'],
                                     episode['link']['label'])
            img = episode['media']['images']['640x360']
            self.addVideoLink(label, video_id, img=img)
        if len(items) >= self.PAGESIZE:
            self.addViewLink(self.NEXT, 'search', page + 1, args)

    def listGrid(self, page, args):
        gridurl = 'https://prod-component-api.nm-services.nelonenmedia.fi/api/component/{gid}?offset={offset}&limit={limit}'
        url = gridurl.format(gid=args['gid'],
                             offset=(page - 1) * self.PAGESIZE,
                             limit=self.PAGESIZE)
        grid = request(url, as_json=True)
        items = grid.get('items', [])
        for item in items:
            link = "https://www.ruutu.fi{}".format(item['link']['href'])
            img = item['media']['images']['640x360']
            if 'video' in link:
                self.addVideoLink(item['link']['label'],
                                  str(item['id']), img=img)
            else:
                self.addViewLink(item['link']['label'], 'seasons', 1, {
                                 'link': link}, img=img)
        if len(items) >= self.PAGESIZE:
            self.addViewLink(self.NEXT, 'grid', page + 1, args)

    def listSeasons(self, page, args):
        for season in self.getSeasons(args['link']):
            self.addViewLink(season['title'], 'season', page, season)

    def listSeason(self, page, args):
        episodes = request(args['link'], as_json=True)
        items = episodes.get('items', [])
        for episode in items:
            ispaid = True
            for r in episode['rights']:
                if r['type'] == 'free' and r['start'] < time.time() < r['end']:
                    ispaid = False
            if ispaid or episode['upcoming']:
                continue
            video_id = str(episode['link']['target']['value'])
            img = episode['media']['images']['640x360']
            self.addVideoLink(episode['title'], video_id, img=img)
        if len(items) >= self.PAGESIZE:
            args['link'] += '&offset={}'.format(page * self.PAGESIZE)
            self.addViewLink(self.NEXT, 'season', page + 1, args)

    def getVideoDetails(self, videoId):
        try:
            url = "https://gatling.nelonenmedia.fi/media-xml-cache?id={vid}"
            content = request(url.format(vid=videoId))
            tree = ET.fromstring(content)
            return {'title': tree.find('.//Program').get('program_name'),
                    'link': tree.find('.//CastMediaFile').text,
                    'image': tree.find('.//Startpicture').get('href'),
                    'description': tree.find('.//Program').get('description')}
        except Exception as e:
            return None

    def handleVideo(self, videoId):
        details = self.getVideoDetails(videoId)
        return {
            'link': details.get('link'),
            'info': {'thumbnailImage': details.get('image', ''),
                     'infoLabels': {'Title': details.get('title'),
                                    'plot': details.get('description')}
                     }
        }

ruutu = RuutuAddon()
lang = ruutu.lang
ruutu.handle()
