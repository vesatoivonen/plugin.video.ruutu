# -*- coding: utf-8 -*-
import urllib.request, urllib.error, urllib.parse
import re
import xml.etree.ElementTree as ET
import json
import time
import resources.lib.xbmcutil as xbmcUtil
import sys
import time
import html
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
        cdata = re.search(r"\[CDATA\[(.*)\]\]", content.decode("utf-8"))
        if cdata:
            series = json.loads(cdata.group(1))
            for page in series["pageStore"]["pages"]:
                pagedata = json.loads(
                    html.unescape(
                        html.unescape(series["pageStore"]["pages"][page]["json"])
                    )
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
                                    "title": item["label"]["text"],
                                }
                            )
                        elif "current_series_has_clips" in params:
                            ret.append(
                                {
                                    "link": self.getClipsLink(
                                        params["current_series_id"]
                                    ),
                                    "title": item["label"]["text"],
                                }
                            )
        return ret

    def addGrid(self, name, gid, page=1):
        self.addViewLink(name, "grid", page, {"gid": gid})

    def handleMain(self, page, args):
        self.addViewLink(
            xbmcUtil.get_translation(30002), "search", 1, {"mode": "video"}
        )
        self.addViewLink(
            xbmcUtil.get_translation(30003), "search", 1, {"mode": "serie"}
        )

        self.addGrid(xbmcUtil.get_translation(30004), 678)
        self.addGrid(xbmcUtil.get_translation(30005), 679)
        self.addGrid(xbmcUtil.get_translation(30006), 733)
        self.addGrid(xbmcUtil.get_translation(30007), 238)
        self.addGrid(xbmcUtil.get_translation(30008), 5333)
        self.addGrid(xbmcUtil.get_translation(30009), 732)
        self.addGrid(xbmcUtil.get_translation(30010), 533)
        self.addGrid(xbmcUtil.get_translation(30011), 602)
        self.addGrid(xbmcUtil.get_translation(30012), 603)

        self.addGrid(xbmcUtil.get_translation(30013), 319)
        self.addGrid(xbmcUtil.get_translation(30014), 398)
        self.addGrid(xbmcUtil.get_translation(30015), 320)
        self.addGrid(xbmcUtil.get_translation(30016), 391)
        self.addGrid(xbmcUtil.get_translation(30017), 392)
        self.addGrid(xbmcUtil.get_translation(30018), 393)
        self.addGrid(xbmcUtil.get_translation(30019), 394)
        self.addGrid(xbmcUtil.get_translation(30020), 395)
        self.addGrid(xbmcUtil.get_translation(30021), 396)
        self.addGrid(xbmcUtil.get_translation(30022), 397)
        self.addGrid(xbmcUtil.get_translation(30023), 584)

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
