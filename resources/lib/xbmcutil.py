# -*- coding: utf-8 -*-
"""
 Utility functions for xbmc. Simplifies common operations on xbmc.
 version 1.1.6
"""

import sys
import urllib.request, urllib.parse, urllib.error
import os
import xbmcplugin
import xbmcgui
import xbmc
import xbmcaddon


class ViewAddonAbstract:
    viewMap = {}
    BASE_PATH = ""
    ADDON_ID = None

    def __init__(self):
        self.addon = xbmcaddon.Addon(id=self.ADDON_ID)
        self.BASE_PATH = self.addon.getAddonInfo("path")

    # self.lang = self.addon.getLocalizedString

    def lang(self, id):
        if id >= 30000 and id <= 30999:
            return self.addon.getLocalizedString(id)
        else:
            return xbmc.getLocalizedString(id)

    def addHandler(self, name, handler):
        if len(self.viewMap) == 0:
            self.viewMap[None] = handler
        self.viewMap[name] = handler

    def setVideoHandler(self, handler):
        videoHandler = handler

    def createContextMenuAction(self, title, action, params={}):
        strParams = urllib.parse.quote_plus(repr(params))
        return (
            title,
            "XBMC.RunPlugin(%s?action=%s&actionParams=%s)"
            % (sys.argv[0], action, strParams),
        )

    def handle(self):
        params = getParams()
        view = getParam(params, "view")
        page = getParam(params, "page")
        if page == None:
            page = 1

        if view == "video":
            link = getParam(params, "link")
            self.playVideo(link)
            return

        elif view == "external":
            hdlFunc = self.viewMap[view]
            hdlFunc(params)
            return

        try:
            hdlFunc = self.viewMap[view]
        except:
            notification("Error", "Could not open view: " + view)
        if "action" in params:
            actParams = eval(urllib.parse.unquote_plus(params["actionParams"]))
            self.handleAction(params["action"], actParams)

        hdlFunc(int(page), params)
        endOfDir()

    def handleAction(self, action, params):
        notification("Unhandled action:", action)

    def playVideo(self, link):
        # xbmc.log("Trying to play URL: " + link, 1)
        details = self.handleVideo(link)
        videoUrl = details.get("link")
        if videoUrl:
            liz = None
            info = details.get("info")
            if info:
                # build the listitem with additional info
                liz = xbmcgui.ListItem(path=videoUrl)
                liz.setArt({"thumb": info.get("thumbnailImage")})
                liz.setInfo(type="Video", infoLabels=info.get("infoLabels"))
            else:
                liz = xbmcgui.ListItem(path=videoUrl)
                liz.setInfo(type="Video", infoLabels={})
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
        else:
            print(("could not play " + link))
            notification(header="Warning", message="Could not find video.")

    # will be overridden on inheritance
    def handleVideo(self, link):
        return link

    def addViewLink(
        self, title, view, page=1, params={}, contextMenu=[], infoLabels={}, img=""
    ):
        u = sys.argv[0] + "?view=" + str(view)
        for key in params.keys():
            u += "&" + key + "=" + urllib.parse.quote_plus(str(params[key]))
        u += "&page=" + str(page)
        icon = "DefaultVideoPlaylists.png"

        liz = xbmcgui.ListItem(title)
        liz.setArt({"icon": icon, "thumb": img})
        liz.setProperty("IsPlayable", "false")
        infoLabels["Title"] = title
        liz.setInfo(type="Video", infoLabels=infoLabels)
        if len(contextMenu) > 0:
            # keep xmbc build it menu items
            liz.addContextMenuItems(contextMenu)
        xbmcplugin.addDirectoryItem(
            handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True
        )

    def addVideoLink(
        self, title, link, img, infoLabels={}, contextMenu=[], videoStreamInfo={}
    ):
        u = sys.argv[0] + "?view=video&link=" + urllib.parse.quote_plus(link)
        # + "&name=" + urllib.quote_plus(title)
        icon = "DefaultVideo.png"
        liz = xbmcgui.ListItem(title)
        liz.setArt({"icon": icon, "thumb": img})
        liz.setProperty("IsPlayable", "true")
        infoLabels["Title"] = title
        liz.setInfo(type="Video", infoLabels=infoLabels)
        liz.addContextMenuItems(contextMenu, True)
        if hasattr(liz, "addStreamInfo"):
            liz.addStreamInfo("video", videoStreamInfo)
        xbmcplugin.addDirectoryItem(
            handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False
        )

    def addDirectVideoLink(self, name, link, img):
        u = link
        icon = "DefaultVideo.png"
        liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=img)
        liz.setProperty("IsPlayable", "true")
        liz.setInfo(type="Video", infoLabels={"Title": name})
        xbmcplugin.addDirectoryItem(
            handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False
        )


def addDir(name, page, autoplay, isPlayable=True):
    u = sys.argv[0] + "?page=" + str(page)
    icon = "DefaultVideoPlaylists.png"
    if autoplay:
        icon = "DefaultVideo.png"
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage="")
    if autoplay and isPlayable:
        liz.setProperty("IsPlayable", "true")
    liz.setInfo(type="Video", infoLabels={"Title": name})
    xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=not autoplay
    )


def endOfDir():
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def addDirLink(name, page, link, autoplay, isPlayable=True):
    u = (
        sys.argv[0]
        + "?page="
        + str(page)
        + "&link="
        + urllib.parse.quote_plus(link)
        + "&name="
        + name
    )
    icon = "DefaultVideoPlaylists.png"
    if autoplay:
        icon = "DefaultVideo.png"
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage="")
    if autoplay and isPlayable:
        liz.setProperty("IsPlayable", "true")
    liz.setInfo(type="Video", infoLabels={"Title": name})
    xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=not autoplay
    )


def addLink(name, url, iconimage):
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    print((sys.argv[1]))

    print((sys.argv))
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
    return ok


def getParams():
    param = {}
    paramstring = sys.argv[2]
    # self.log.debug('raw param string: ' + paramstring)
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace("?", "")
        if params[len(params) - 1] == "/":
            params = params[0 : len(params) - 2]
        pairsofparams = cleanedparams.split("&")
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split("=")
            if (len(splitparams)) == 2:
                param[splitparams[0]] = urllib.parse.unquote_plus(splitparams[1])
    return param


def getParam(params, name):
    try:
        result = params[name]
        result = result
        # result = urllib.unquote_plus(result)
        return result
    except:
        return None


def notification(header="", message="", sleep=5000):
    """Will display a notification dialog with the specified header and message,
    in addition you can set the length of time it displays in milliseconds and a icon image.
    """
    xbmc.executebuiltin("XBMC.Notification(%s,%s,%i)" % (header, message, sleep))


def get_translation(string_id):
    src = xbmc if string_id < 30000 else xbmcaddon.Addon()
    return src.getLocalizedString(string_id)
