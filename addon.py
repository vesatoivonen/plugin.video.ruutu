# -*- coding: utf-8 -*-
import urllib.request, urllib.error, urllib.parse
import re
import xml.etree.ElementTree as ET
import json
import time
import resources.lib.xbmcutil as xbmcUtil
import sys
import time
from html.parser import HTMLParser
import importlib

importlib.reload(sys)


def request(url, as_json=False):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    req.add_header("content-type", "application/json")
    try:
        response = urllib.request.urlopen(req)
        content = response.read()
        response.close()
        if as_json:
            return json.loads(content)
        return content
    except urllib.error.HTTPError:
        return []


class RuutuAddon(xbmcUtil.ViewAddonAbstract):
    ADDON_ID = "plugin.video.ruutu"

    def __init__(self):
        xbmcUtil.ViewAddonAbstract.__init__(self)
        self.NEXT = ">>> %s >>>" % self.lang(33078)
        self.PAGESIZE = 15

        self.addHandler(None, self.handleMain)
        self.addHandler("grid", self.listGrid)
        self.addHandler("seasons", self.listSeasons)
        self.addHandler("season", self.listSeason)
        self.addHandler("search", self.handleSearch)

    def getSeasonLink(self, seasonId):
        url = "https://prod-component-api.nm-services.nelonenmedia.fi/api/component/26004?limit={limit}&current_season_id={sid}&app=ruutu&client=web"
        return url.format(limit=self.PAGESIZE, sid=seasonId)

    def getClipsLink(self, seriesId):
        url = "https://prod-component-api.nm-services.nelonenmedia.fi/api/component/26005?limit={limit}&current_series_has_clips=true&current_series_id={sid}&app=ruutu&client=web"
        return url.format(limit=self.PAGESIZE, sid=seriesId)

    def getSeasons(self, seriesUrl):
        content = request(seriesUrl)
        ret = []
        h = HTMLParser()
        cdata = re.search(r"\[CDATA\[(.*)\]\]", content.decode("utf-8"))
        if cdata:
            series = json.loads(cdata.group(1))
            for page in series["pageStore"]["pages"]:
                pagedata = json.loads(
                    h.unescape(h.unescape(series["pageStore"]["pages"][page]["json"]))
                )
                for component in pagedata["components"]:
                    if component["type"] == "Container":
                        continue
                    for item in component["content"]["items"]:
                        if (
                            item["type"] != "Grid"
                            or "content" not in item
                            or "query" not in item["content"]
                        ):
                            continue
                        params = item["content"]["query"]["params"]
                        if "current_season_id" in params:
                            ret.append(
                                {
                                    "link": self.getSeasonLink(
                                        params["current_season_id"]
                                    ),
                                    "title": item["link"]["label"],
                                }
                            )
                        elif "current_series_has_clips" in params:
                            ret.append(
                                {
                                    "link": self.getClipsLink(
                                        params["current_series_id"]
                                    ),
                                    "title": item["link"]["label"],
                                }
                            )
        return ret

    def addGrid(self, name, gid, page=1):
        self.addViewLink(name, "grid", page, {"gid": gid})

    def handleMain(self, page, args):
        self.addViewLink("Hae jaksoa", "search", 1, {"mode": "video"})
        self.addViewLink("Hae sarjaa", "search", 1, {"mode": "serie"})

        self.addGrid("Katsotuimmat", 678)
        self.addGrid("Kotimainen viihde", 679)
        self.addGrid("Kotimainen reality", 733)
        self.addGrid("Elokuvat", 238)
        self.addGrid("Ruutu alkuperäissarjat", 5333)
        self.addGrid("Dokumentit", 732)
        self.addGrid("Jännitys ja draama", 533)
        self.addGrid("Lifestyle", 602)
        self.addGrid("Kansainvälinen reality ja viihde", 603)

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
        """
        337 for videos
        338 for series
        """
        mode = 337 if args["mode"] == "video" else 338
        url = "https://prod-component-api.nm-services.nelonenmedia.fi/api/component/{mode}?offset={offset}&limit={limit}&search_term={query}&app=ruutu&client=web"

        if "query" not in args:
            keyboard = xbmc.Keyboard()
            keyboard.setHeading(self.lang(30080))
            keyboard.doModal()
            if keyboard.isConfirmed() and keyboard.getText() != "":
                query = keyboard.getText()
                args["query"] = query

        url = url.format(
            offset=(page - 1) * self.PAGESIZE,
            limit=self.PAGESIZE,
            mode=mode,
            query=args["query"],
        )
        items = request(url, as_json=True).get("items", [])
        for item in items:
            if item.get("sticker"):
                continue
            img = item["media"]["images"]["640x360"]
            if "video" in item["link"]["href"]:
                video_id = str(item["link"]["target"]["value"])
                label = "{} - {}".format(item.get("footer"), item["link"]["label"])
                self.addVideoLink(
                    label, video_id, img=img, infoLabels={"plot": item["description"]}
                )
            else:
                link = "https://www.ruutu.fi{}".format(item["link"]["href"])
                self.addViewLink(
                    item["link"]["label"],
                    "seasons",
                    page,
                    {"link": link},
                    img=img,
                    infoLabels={"plot": item["description"]},
                )
        if len(items) >= self.PAGESIZE:
            self.addViewLink(self.NEXT, "search", page + 1, args)

    def listGrid(self, page, args):
        gridurl = "https://prod-component-api.nm-services.nelonenmedia.fi/api/component/{gid}?offset={offset}&limit={limit}&app=ruutu&client=web"
        url = gridurl.format(
            gid=args["gid"], offset=(page - 1) * self.PAGESIZE, limit=self.PAGESIZE
        )
        grid = request(url, as_json=True)
        items = grid.get("items", [])
        for item in items:
            if item.get("sticker"):
                continue
            link = "https://www.ruutu.fi{}".format(item["link"]["href"])
            img = item["media"]["images"]["640x360"]
            if "video" in link:
                self.addVideoLink(
                    item["link"]["label"],
                    str(item["id"]),
                    img=img,
                    infoLabels={"plot": item["description"]},
                )
            else:
                self.addViewLink(
                    item["link"]["label"],
                    "seasons",
                    page,
                    {"link": link},
                    img=img,
                    infoLabels={"plot": item["description"]},
                )
        if len(items) >= self.PAGESIZE:
            self.addViewLink(self.NEXT, "grid", page + 1, args)

    def listSeasons(self, page, args):
        for season in self.getSeasons(args["link"]):
            self.addViewLink(season["title"], "season", page, season)

    def listSeason(self, page, args):
        pageurl = args["link"] + "&offset={}".format((int(page) - 1) * self.PAGESIZE)
        episodes = request(pageurl, as_json=True)
        items = episodes.get("items", [])
        for episode in items:
            ispaid = episode.get("rights") is not None
            for r in episode.get("rights", []):
                if r["type"] == "free" and r["start"] < time.time() < r["end"]:
                    ispaid = False
            if ispaid or episode.get("upcoming"):
                continue
            video_id = str(episode["link"]["target"]["value"])
            img = episode["media"]["images"]["640x360"]
            self.addVideoLink(
                episode["title"],
                video_id,
                img=img,
                infoLabels={"plot": episode["description"]},
            )
        if len(items) >= self.PAGESIZE:
            self.addViewLink(self.NEXT, "season", page + 1, args)

    def getVideoDetails(self, videoId):
        try:
            url = "https://gatling.nelonenmedia.fi/media-xml-cache?id={vid}&v=3"
            content = request(url.format(vid=videoId))
            tree = ET.fromstring(content)
            if tree.find(".//Paid").text == "1":
                return None
            return {
                "title": tree.find(".//Metadata").find("ProgramName").text,
                "link": tree.find(".//StreamURLs").find("Cast").text,
                "image": tree.find(".//Images")
                .find("Image[@resolution='640x360']")
                .get("url"),
                "description": tree.find(".//Metadata").find("Description").text,
            }
        except Exception as e:
            return None

    def getToken(self, link):
        try:
            url = "https://gatling.nelonenmedia.fi/auth/access/v2?stream={link}&timestamp={ts}"
            content = request(url.format(link=link, ts=int(time.time())))
            return content
        except Exception as e:
            return None

    def handleVideo(self, videoId):
        details = self.getVideoDetails(videoId)
        if details is None:
            return {}
        return {
            "link": self.getToken(details.get("link")),
            "info": {
                "thumbnailImage": details.get("image", ""),
                "infoLabels": {
                    "Title": details.get("title"),
                    "plot": details.get("description"),
                },
            },
        }


ruutu = RuutuAddon()
lang = ruutu.lang
ruutu.handle()
