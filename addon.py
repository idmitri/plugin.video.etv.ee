#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
#      Copyright (C) 2015 Yllar Pajus
#      http://ku.uk.is
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
from datetime import datetime, timedelta
import locale
import os
import sys
import urlparse
import urllib2
import json

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import buggalo

try:
  locale.setlocale(locale.LC_ALL, 'et_EE.UTF-8')
except locale.Error:
  locale.setlocale(locale.LC_ALL, 'C')

__settings__  = xbmcaddon.Addon(id='plugin.video.etv.ee')

DAYS = int(__settings__.getSetting('days'))
if DAYS < 1:
  DAYS = 1

class Logger:
  def write(data):
    xbmc.log(data)
  write = staticmethod(write)
sys.stdout = Logger
sys.stderr = Logger

class EtvException(Exception):
  pass

class Etv(object):
  def downloadUrl(self,url):
    for retries in range(0, 5):
      try:
	r = urllib2.Request(url.encode('iso-8859-1', 'replace'))
	r.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:10.0.2) Gecko/20100101 Firefox/10.0.2')
	u = urllib2.urlopen(r, timeout = 30)
	contents = u.read()
	u.close()
	return contents
      except Exception, ex:
        if retries > 5:
	  raise EtvException(ex)
	
  def listChannels(self):
    items = list()
    item = xbmcgui.ListItem('ETV', iconImage=LOGOETV)
    item.setProperty('Fanart_Image', FANART)
    items.append((PATH + '?channel=%s' % 'etv', item, True))
    item = xbmcgui.ListItem('ETV2', iconImage=LOGOETV2)
    item.setProperty('Fanart_Image', FANART2)
    items.append((PATH + '?channel=%s' % 'etv2', item, True))
    item = xbmcgui.ListItem('ETV pluss', iconImage=LOGOETV)
    item.setProperty('Fanart_Image', FANART)
    items.append((PATH + '?channel=%s' % 'etvpluss', item, True))
    item = xbmcgui.ListItem('ETV otse', iconImage=LOGOETV)
    item.setProperty('Fanart_Image', FANART)
    item.setInfo('video', infoLabels={"Title": "ETV otse"})
    item.setProperty('IsPlayable', 'true')
    items.append((PATH + '?vaata=rtmp://wowza3.err.ee:80/live/%s' % 'etv', item, False))
    item = xbmcgui.ListItem('ETV2 otse', iconImage=LOGOETV2)
    item.setProperty('Fanart_Image', FANART2)
    item.setInfo('video', infoLabels={"Title": "ETV2 otse"})
    item.setProperty('IsPlayable', 'true')
    items.append((PATH + '?vaata=rtmp://wowza3.err.ee:80/live/%s' % 'etv2', item, False))
    item = xbmcgui.ListItem('ETV pluss otse', iconImage=LOGOETV)
    item.setProperty('Fanart_Image', FANART)
    item.setInfo('video', infoLabels={"Title": "ETV pluss otse"})
    item.setProperty('IsPlayable', 'true')
    items.append((PATH + '?vaata=rtmp://wowza3.err.ee:80/live/%s' % 'etvpluss', item, False))
    xbmcplugin.addDirectoryItems(HANDLE, items)
    xbmcplugin.endOfDirectory(HANDLE)

    
  def listDates(self,channel):
    items = list()

    tana = "%s %s" % (ADDON.getLocalizedString(30003), datetime.now().strftime('%Y-%m-%d'))
    tanad = datetime.now().strftime('%Y-%m-%d')
    item = xbmcgui.ListItem(tana, iconImage=FANART)
    item.setProperty('Fanart_Image', FANART)
    items.append((PATH + '?channel=%s&date=%s' % (channel,tanad), item, True))
    
    for paevad in range(1,DAYS):
      paev = datetime.now() - timedelta(days=paevad)
      paevd =  paev.strftime('%A %Y-%m-%d')
      paev = paev.strftime('%Y-%m-%d')
      item = xbmcgui.ListItem(paevd, iconImage=FANART)
      item.setProperty('Fanart_Image', FANART)
      items.append((PATH + '?channel=%s&date=%s' % (channel,paev), item, True))
    xbmcplugin.addDirectoryItems(HANDLE, items)
    xbmcplugin.endOfDirectory(HANDLE)
  
  def listSchedule(self,channel,date):
    year,month,day = date.split("-")
    url = 'http://%s.err.ee/api/loader/GetTimelineDay/?year=%s&month=%s&day=%s' % (channel,year,month,day)
    buggalo.addExtraData('url', url)
    html = self.downloadUrl(url)
    if not html:
      raise EtvException(ADDON.getLocalizedString(203))

    html = json.loads(html)
    items = list()
    for s in html:
      if s['Image']:
        fanart = 'http://static.err.ee/gridfs/%s?width=720' % s['Image']
      else:
        fanart = FANART
      title = s['Header']
      plot = s['Lead']
      
      infoLabels = {
	'plot' : plot,
	'title' : title
      }

      item = xbmcgui.ListItem(title, iconImage = fanart)
      item.setInfo('video', infoLabels)
      item.setProperty('IsPlayable', 'true')
      item.setProperty('Fanart_Image', fanart)
      items.append((PATH + '?vaata=%s' %  s['Id'], item))
    xbmc.executebuiltin("Container.SetViewMode(500)")
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addDirectoryItems(HANDLE, items)
    xbmcplugin.endOfDirectory(HANDLE)     
    
  def getMediaLocation(self,key):
    url = "http://etv.err.ee/api/loader/GetTimeLineContent/%s" % key
    buggalo.addExtraData('url', url)
    html = self.downloadUrl(url)
    if html:
      html = json.loads(html)
      for url in html['MediaSources']:
        return 'rtmp%s' % url['Content'].replace('@','_definst_/')
      raise EtvException(ADDON.getLocalizedString(202))
    else:
      raise EtvException(ADDON.getLocalizedString(202))
    
  def playStream(self,vaata):
    if vaata == '00000000-0000-0000-0000-000000000000':
      raise EtvException(ADDON.getLocalizedString(202))
    if ":80/live" in vaata:
      saade = vaata
    else:
      saade = EtvAddon.getMediaLocation(vaata)
    buggalo.addExtraData('saade', saade)
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    
    item = xbmcgui.ListItem(saade, iconImage = ICON, path = saade)
    playlist.add(saade,item)
    xbmcplugin.setResolvedUrl(HANDLE, True, item)

  def displayError(self, message = 'n/a'):
    heading = buggalo.getRandomHeading()
    line1 = ADDON.getLocalizedString(200)
    line2 = ADDON.getLocalizedString(201)
    xbmcgui.Dialog().ok(heading, line1, line2, message)
    
if __name__ == '__main__':
  ADDON = xbmcaddon.Addon()
  PATH = sys.argv[0]
  HANDLE = int(sys.argv[1])
  PARAMS = urlparse.parse_qs(sys.argv[2][1:])
  
  ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
  FANART = os.path.join(ADDON.getAddonInfo('path'), 'etv.jpg')
  FANART2 = os.path.join(ADDON.getAddonInfo('path'), 'etv2.jpg')
  LOGOETV = os.path.join(ADDON.getAddonInfo('path'), 'etv-logo.png')
  LOGOETV2 = os.path.join(ADDON.getAddonInfo('path'), 'etv2-logo.png')
  
  CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
  if not os.path.exists(CACHE_PATH):
    os.makedirs(CACHE_PATH)
    

  buggalo.SUBMIT_URL = 'http://ku.uk.is/exception/submit.php'
  
  EtvAddon = Etv()
  try:
    if PARAMS.has_key('channel') and PARAMS.has_key('date'):
      EtvAddon.listSchedule(PARAMS['channel'][0], PARAMS['date'][0])
    elif PARAMS.has_key('channel'):
      EtvAddon.listDates(PARAMS['channel'][0])
    elif PARAMS.has_key('vaata'):
      EtvAddon.playStream(PARAMS['vaata'][0])
    else:
      EtvAddon.listChannels()
  except EtvException, ex:
    EtvAddon.displayError(str(ex))
  except Exception:
    buggalo.onExceptionRaised()
