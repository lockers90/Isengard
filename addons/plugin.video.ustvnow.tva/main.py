'''
    USTVnow Plus Add-on
    
    This version of USTVnow has been built by combining the best of all
    available version of USTVnow found online. This version has been streamlined 
    to use the USTVnow API directly to avoid many of the issues in previous versions.

    The following developers have all contributed to this version directly or indirectly.

    mhancoc7, t0mm0, jwdempsey, esxbr, Lunatixz, yrabl, ddurdle

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from resources.lib import Addon, ustvnow_plus
import sys, os, urllib, urllib2
import json, random
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

addon       = xbmcaddon.Addon()
addonname   = addon.getAddonInfo('name')
addonid   = addon.getAddonInfo('id')
plugin_path = xbmcaddon.Addon(id=addonid).getAddonInfo('path')

Addon.plugin_url = sys.argv[0]
Addon.plugin_handle = int(sys.argv[1])
Addon.plugin_queries = Addon.parse_query(sys.argv[2][1:])

setup = Addon.get_setting('setup')
setup_new = Addon.get_setting('setup_new')
email = Addon.get_setting('email')
password = Addon.get_setting('password')
ustv = ustvnow_plus.Ustvnow(email, password)

dlg = xbmcgui.Dialog()

Addon.log('plugin url: ' + Addon.plugin_url)
Addon.log('plugin queries: ' + str(Addon.plugin_queries))
Addon.log('plugin handle: ' + str(Addon.plugin_handle)) 

quality_type = int(Addon.get_setting('quality'))

if setup != 'true':
    dlg.ok(Addon.get_string(30000),Addon.get_string(20002),Addon.get_string(20003))
    # Enter Email
    retval = dlg.input(Addon.get_string(20004), type=xbmcgui.INPUT_ALPHANUM)
    if retval and len(retval) > 0:
        Addon.set_setting('email', str(retval))
        email = Addon.get_setting('email')
    # Enter Password
    retval = dlg.input(Addon.get_string(20005), type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
    if retval and len(retval) > 0:
        Addon.set_setting('password', str(retval))
        password = Addon.get_setting('password')
    if len(Addon.get_setting('email')) > 0 and len(Addon.get_setting('password')) > 0:
        Addon.set_setting('setup', 'true')
        dlg.ok(Addon.get_string(30000), Addon.get_string(200001), Addon.get_string(200000))
    else:
        dlg.ok(Addon.get_string(30000), Addon.get_string(20002),Addon.get_string(20003))
elif setup_new != 'true':
    dlg.ok(Addon.get_string(30000),Addon.get_string(50000),Addon.get_string(50001))
    Addon.set_setting('setup_new', 'true')

mode = Addon.plugin_queries['mode']

if mode == 'main':
    Addon.log(mode)
    ustv.build_main()

elif mode == 'live':
    stream_type = 'rtmp'
    channels = ustv.get_channels(quality_type, stream_type)
    if channels:
        for c in channels:
            rURL = "plugin://plugin.video.ustvnow.tva/?name=" + c['name'] + "&mode=play"
            name = c["name"];
            if Addon.get_setting('logo') == '0':
                logo = c["poster_url"];
                poster_url = xbmc.translatePath(os.path.join(plugin_path, 'resources', 'images', c['name']+'.png'))
            else:
                logo = xbmc.translatePath(os.path.join(plugin_path, 'resources', 'images', c['name']+'.png'))
                poster_url = c["poster_url"];
            episode_title = c["episode_title"];
            title = c["title"];
            plot = c["plot"].replace("&amp;", "&").replace('&quot;','"');
            mediatype = c["mediatype"];
            if mediatype != "movie":
                tvshowtitle = title
            if name == 'AE':
                name = 'A&E'
            if name == 'MY9':
                name = 'My9'
            if episode_title != "":
                title = '%s - %s - %s (Started at %s)' % (name, (title).replace('&amp;','&').replace('&quot;','"'), (episode_title).replace('&amp;','&').replace('&quot;','"').replace(';',' -'), c['event_date_time'])
            else:
                title = '%s - %s (Started at %s)' % (name, (title).replace('&amp;','&').replace('&quot;','"'), c['event_date_time'])
            cm_refresh = (Addon.get_string(30007), 
                      'XBMC.RunPlugin(%s/?mode=refresh)' % 
                           (Addon.plugin_url))
            cm_rec = (Addon.get_string(30008), 
                      'XBMC.RunPlugin(%s/?mode=record&rec=%s&set=%s&mt=%s)' % 
                           (Addon.plugin_url, urllib.quote(c['rec_url']),urllib.quote(c['set_url']),urllib.quote(c['mediatype'])))
            if Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'true':
                cm_menu = [cm_refresh, cm_rec]
            elif Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'false' and name in ['CW','ABC','FOX','PBS','CBS','NBC','My9']:
                cm_menu = [cm_refresh, cm_rec]
            else:
                cm_menu = [cm_refresh]
            Addon.add_video_item(rURL,
            
                                 {'title': title,
                                 'plot': plot,
                                 'mediatype': mediatype,
                                 'tvshowtitle': tvshowtitle},
                                 img=poster_url, fanart=logo, playable=c['playable'], cm=cm_menu, cm_replace=True)
            xbmcplugin.setContent(Addon.plugin_handle, 'movie')

elif mode == 'recordings':
    stream_type = ['rtsp', 'rtmp'][int(Addon.get_setting('rec_stream_type'))]
    recordings_quality = int(Addon.get_setting('quality'))
    # This ensures that recordings are 1024kbps or less
    if recordings_quality == 3:
        recordings_quality = 2
    recordings = ustv.get_recordings(int(recordings_quality), 
                                     stream_type, 'recordings')
        
    if recordings:
        for r in recordings:
            channel = r['channel']
            if r['channel'] == 'AE':
                channel = 'A&E'
            if r['channel'] == 'MY9':
                channel = 'My9'
            if r['episode_title'] != "":
                title = '%s - %s (Recorded: %s on %s) - (Expires: %s)' % (r['title'], r['episode_title'], r['event_date_time'], channel ,r['expire_date_time'])
                title = title.replace('&amp;','&').replace('&quot;','"')
            else:
                title = '%s (Recorded: %s on %s) - (Expires: %s)' % (r['title'], r['event_date_time'], channel ,r['expire_date_time'])
                title = title.replace('&amp;','&').replace('&quot;','"')

            logo = xbmc.translatePath(os.path.join(plugin_path, 'resources', 'images', r['channel']+'.png'))
            poster_url = r["icon"];
            dvrtimertype = r['dvrtimertype']
            mediatype = r['mediatype']
            cm_refresh = (Addon.get_string(30007),
                  'XBMC.RunPlugin(%s/?mode=refresh)' % 
                       (Addon.plugin_url))
            cm_set_recurring = (Addon.get_string(30026), 
                      'XBMC.RunPlugin(%s/?mode=set&set=%s)' % 
                           (Addon.plugin_url, urllib.quote(r['set_url'])))
            cm_del_recurring = (Addon.get_string(30022), 
                      'XBMC.RunPlugin(%s/?mode=remove&remove=%s)' % 
                           (Addon.plugin_url, urllib.quote(r['remove_url'])))
            cm_del = (Addon.get_string(30004), 
                      'XBMC.RunPlugin(%s/?mode=delete&del=%s)' % 
                           (Addon.plugin_url, urllib.quote(r['del_url'])))
            if Addon.get_setting('rec_live') == 'true' and dvrtimertype == 0 and Addon.get_setting('dvr') == 'true' and mediatype != 'MV':
                cm_menu = [cm_refresh, cm_set_recurring, cm_del]
            elif  Addon.get_setting('rec_live') == 'true' and dvrtimertype != 0 and Addon.get_setting('dvr') == 'true' and mediatype != 'MV':
                cm_menu = [cm_refresh, cm_del_recurring]
            elif  Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'true' and mediatype == 'MV':
                cm_menu = [cm_refresh, cm_del]
            elif Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'false':
                cm_menu = [cm_refresh, cm_del]
            else:
                cm_menu = [cm_refresh]
            Addon.add_video_item(r['stream_url'], {'title': title, 
                                                   'plot': r['plot'],
                                                   'plotoutline': r['synopsis'],
                                                   'tvshowtitle': r['tvshowtitle'],
                                                   'dateadded': r['rec_date']},
                                 img=poster_url, fanart=logo, cm=cm_menu, cm_replace=True, playable=r['playable'])
        xbmcplugin.setContent(Addon.plugin_handle, 'movie')

elif mode == 'scheduled':
    stream_type = 'rtmp'
    recordings_quality = int(Addon.get_setting('quality'))
    # This ensures that recordings are 1024kbps or less
    if recordings_quality == 3:
        recordings_quality = 2
    recordings = ustv.get_recordings(int(recordings_quality), 
                                     stream_type, 'scheduled')
        
    if recordings:
        for r in recordings:
            channel = r['channel']
            if r['channel'] == 'AE':
                channel = 'A&E'
            if r['channel'] == 'MY9':
                channel = 'My9'
            if r['episode_title'] != "":
                title = '%s - %s (%s on %s)' % (r['title'], r['episode_title'], r['event_date_time'], channel)
                title = title.replace('&amp;','&').replace('&quot;','"')
            else:
                title = '%s (%s on %s)' % (r['title'], r['event_date_time'], channel)
                title = title.replace('&amp;','&').replace('&quot;','"')
            plot = '[B]' + r['title'] + '[/B]'
            logo = xbmc.translatePath(os.path.join(plugin_path, 'resources', 'images', r['channel']+'.png'))
            poster_url = r["icon"];
            dvrtimertype = r['dvrtimertype']
            mediatype = r['mediatype']
            cm_refresh = (Addon.get_string(30007), 
                  'XBMC.RunPlugin(%s/?mode=refresh)' % 
                       (Addon.plugin_url))
            cm_set_recurring = (Addon.get_string(30026), 
                      'XBMC.RunPlugin(%s/?mode=set&set=%s)' % 
                           (Addon.plugin_url, urllib.quote(r['set_url'])))
            cm_del_recurring = (Addon.get_string(30022), 
                      'XBMC.RunPlugin(%s/?mode=remove&remove=%s)' % 
                           (Addon.plugin_url, urllib.quote(r['remove_url'])))
            cm_del = (Addon.get_string(30004), 
                      'XBMC.RunPlugin(%s/?mode=delete&del=%s)' % 
                           (Addon.plugin_url, urllib.quote(r['del_url'])))
            if Addon.get_setting('rec_live') == 'true' and dvrtimertype == 0 and Addon.get_setting('dvr') == 'true' and mediatype != 'MV':
                cm_menu = [cm_refresh, cm_set_recurring, cm_del]
            elif  Addon.get_setting('rec_live') == 'true' and dvrtimertype != 0 and Addon.get_setting('dvr') == 'true' and mediatype != 'MV':
                cm_menu = [cm_refresh, cm_del_recurring]
            elif  Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'true' and mediatype == 'MV':
                cm_menu = [cm_refresh, cm_del]
            elif Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'false':
                cm_menu = [cm_refresh, cm_del]
            else:
                cm_menu = [cm_refresh]
            Addon.add_list_item(r['title'], {'title': title, 'plot': plot, 
                                                   'dateadded': r['rec_date']},
                                 img=poster_url, fanart=logo, cm=cm_menu, cm_replace=True, playable=False)
        xbmcplugin.setContent(Addon.plugin_handle, 'movie')

elif mode == 'recurring':
    stream_type = 'rtmp'
    recordings_quality = int(Addon.get_setting('quality'))
    # This ensures that recordings are 1024kbps or less
    if recordings_quality == 3:
        recordings_quality = 2
    recordings = ustv.get_recordings(int(recordings_quality), 
                                     stream_type, 'recurring')
        
    if recordings:
        for r in recordings:
            cm_del_recurring = (Addon.get_string(30022), 
                      'XBMC.RunPlugin(%s/?mode=remove&remove=%s)' % 
                           (Addon.plugin_url, urllib.quote(r['remove_url'])))
            cm_refresh = (Addon.get_string(30007), 
                  'XBMC.RunPlugin(%s/?mode=refresh)' % 
                       (Addon.plugin_url))
            channel = r['channel']
            if r['channel'] == 'AE':
                channel = 'A&E'
            if r['channel'] == 'MY9':
                channel = 'My9'
            title = '%s (%s)' % (r['title'], channel)
            title = title.replace('&amp;','&').replace('&quot;','"')
            plot = '[B]' + r['title'] + '[/B]'
            logo = xbmc.translatePath(os.path.join(plugin_path, 'resources', 'images', r['channel']+'.png'))
            poster_url = r["icon"];
            if Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'true':
                cm_menu = [cm_refresh, cm_del_recurring]
            else:
                cm_menu = [cm_refresh]
            Addon.add_list_item(r['title'], {'title': title, 'plot': plot},
                                 img=poster_url, fanart=logo, cm=cm_menu, cm_replace=True, playable=False)
        xbmcplugin.setContent(Addon.plugin_handle, 'movie')

elif mode == 'movies_now':
    stream_type = 'rtmp'
    now = ustv.get_movies(int(quality_type), 
                                     stream_type, 'now')
        
    if now:
        for r in now:
            channel = r['channel']
            rURL = "plugin://plugin.video.ustvnow.tva/?name=" + r['channel'] + "&mode=play"
            if r['channel'] == 'AE':
                channel = 'A&E'
            if r['channel'] == 'MY9':
                channel = 'My9'

            title = '%s (Started at %s on %s)' % (r['title'], r['event_date_time_now'], channel)
            title = title.replace('&amp;','&').replace('&quot;','"')

            logo = xbmc.translatePath(os.path.join(plugin_path, 'resources', 'images', r['channel']+'.png'))
            poster_url = r["icon"];
            dvrtimertype = r['dvrtimertype']
            mediatype = r['mediatype']
            cm_refresh = (Addon.get_string(30007),
                  'XBMC.RunPlugin(%s/?mode=refresh)' % 
                       (Addon.plugin_url))
            cm_rec = (Addon.get_string(30008), 
                      'XBMC.RunPlugin(%s/?mode=record&rec=%s&mt=%s)' % 
                           (Addon.plugin_url, urllib.quote(r['rec_url']),urllib.quote(r['mediatype'])))
            if Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'true':
                cm_menu = [cm_refresh, cm_rec]
            elif Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'false' and channel in ['CW','ABC','FOX','PBS','CBS','NBC','My9']:
                cm_menu = [cm_refresh, cm_rec]
            else:
                cm_menu = [cm_refresh]
            Addon.add_video_item(rURL, {'title': title,'plot': r['plot']},
                                 img=poster_url, fanart=logo, cm=cm_menu, cm_replace=True, playable=r['playable'])
        xbmcplugin.setContent(Addon.plugin_handle, 'movie')

elif mode == 'movies_today':
    stream_type = 'rtmp'
    today = ustv.get_movies(int(quality_type), 
                                     stream_type, 'today')
        
    if today:
        for r in today:
            channel = r['channel']
            if r['channel'] == 'AE':
                channel = 'A&E'
            if r['channel'] == 'MY9':
                channel = 'My9'

            title = '%s (%s on %s)' % (r['title'], r['event_date_time'], channel)
            title = title.replace('&amp;','&').replace('&quot;','"')

            logo = xbmc.translatePath(os.path.join(plugin_path, 'resources', 'images', r['channel']+'.png'))
            poster_url = r["icon"];
            dvrtimertype = r['dvrtimertype']
            mediatype = r['mediatype']
            cm_refresh = (Addon.get_string(30007), 
                  'XBMC.RunPlugin(%s/?mode=refresh)' % 
                       (Addon.plugin_url))
            cm_rec = (Addon.get_string(30008), 
                      'XBMC.RunPlugin(%s/?mode=record&rec=%s&mt=%s)' % 
                           (Addon.plugin_url, urllib.quote(r['rec_url']),urllib.quote(r['mediatype'])))
            
            if Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'true':
                cm_menu = [cm_refresh, cm_rec]
            elif Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'false' and channel in ['CW','ABC','FOX','PBS','CBS','NBC','My9']:
                cm_menu = [cm_refresh, cm_rec]
            else:
                cm_menu = [cm_refresh]
            
            Addon.add_list_item(r['title'], {'title': title,'plot': r['plot']},
                                 img=poster_url, fanart=logo, cm=cm_menu, cm_replace=True, playable=r['playable'])
        xbmcplugin.setContent(Addon.plugin_handle, 'movie')

elif mode == 'movies_later':
    stream_type = 'rtmp'
    later = ustv.get_movies(int(quality_type), 
                                     stream_type, 'later')
        
    if later:
        for r in later:
            channel = r['channel']
            if r['channel'] == 'AE':
                channel = 'A&E'
            if r['channel'] == 'MY9':
                channel = 'My9'

            title = '%s (%s on %s)' % (r['title'], r['event_date_time'], channel)
            title = title.replace('&amp;','&').replace('&quot;','"')
 
            logo = xbmc.translatePath(os.path.join(plugin_path, 'resources', 'images', r['channel']+'.png'))
            poster_url = r["icon"];
            dvrtimertype = r['dvrtimertype']
            mediatype = r['mediatype']
            cm_refresh = (Addon.get_string(30007), 
                  'XBMC.RunPlugin(%s/?mode=refresh)' % 
                       (Addon.plugin_url))
            cm_rec = (Addon.get_string(30008), 
                      'XBMC.RunPlugin(%s/?mode=record&rec=%s&mt=%s)' % 
                           (Addon.plugin_url, urllib.quote(r['rec_url']),urllib.quote(r['mediatype'])))
            
            if Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'true':
                cm_menu = [cm_refresh, cm_rec]
            elif Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'false' and channel in ['CW','ABC','FOX','PBS','CBS','NBC','My9']:
                cm_menu = [cm_refresh, cm_rec]
            else:
                cm_menu = [cm_refresh]
            
            Addon.add_list_item(r['title'], {'title': title,'plot': r['plot']},
                                 img=poster_url, fanart=logo, cm=cm_menu, cm_replace=True, playable=False)
        xbmcplugin.setContent(Addon.plugin_handle, 'movie')

elif mode == 'sports_now':
    stream_type = 'rtmp'
    channels = ustv.get_sports(quality_type, stream_type, 'now')
    if channels:
        for c in channels:
            rURL = "plugin://plugin.video.ustvnow.tva/?name=" + c['name'] + "&mode=play"
            name = c["name"];

            logo = xbmc.translatePath(os.path.join(plugin_path, 'resources', 'images', c['name']+'.png'))
            poster_url = c["poster_url"];
            title = c["title"];
            plot = c["plot"].replace("&amp;", "&").replace('&quot;','"');
            mediatype = c["mediatype"];
            if mediatype != "movie":
                tvshowtitle = title
            if name == 'AE':
                name = 'A&E'
            if name == 'MY9':
                name = 'My9'

            title = '%s (Started at %s on %s)' % (c['title'], c['event_date_time_now'], name)
            cm_refresh = (Addon.get_string(30007), 
                      'XBMC.RunPlugin(%s/?mode=refresh)' % 
                           (Addon.plugin_url))
            cm_rec = (Addon.get_string(30008), 
                      'XBMC.RunPlugin(%s/?mode=record&rec=%s&set=%s&mt=%s)' % 
                           (Addon.plugin_url, urllib.quote(c['rec_url']),urllib.quote(c['set_url']),urllib.quote(c['mediatype'])))
            if Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'true':
                cm_menu = [cm_refresh, cm_rec]
            elif Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'false' and name in ['CW','ABC','FOX','PBS','CBS','NBC','My9']:
                cm_menu = [cm_refresh, cm_rec]
            else:
                cm_menu = [cm_refresh]
            Addon.add_video_item(rURL,
            
                                 {'title': title,
                                 'plot': plot,
                                 'mediatype': mediatype,
                                 'tvshowtitle': tvshowtitle},
                                 img=poster_url, fanart=logo, playable=c['playable'], cm=cm_menu, cm_replace=True)
            xbmcplugin.setContent(Addon.plugin_handle, 'movie')

elif mode == 'sports_today':
    stream_type = 'rtmp'
    channels = ustv.get_sports(quality_type, stream_type, 'today')
    if channels:
        for c in channels:
            rURL = "plugin://plugin.video.ustvnow.tva/?name=" + c['name'] + "&mode=play"
            name = c["name"];

            logo = xbmc.translatePath(os.path.join(plugin_path, 'resources', 'images', c['name']+'.png'))
            poster_url = c["poster_url"];
            title = c["title"];
            plot = c["plot"].replace("&amp;", "&").replace('&quot;','"');
            mediatype = c["mediatype"];
            if mediatype != "movie":
                tvshowtitle = title
            if name == 'AE':
                name = 'A&E'
            if name == 'MY9':
                name = 'My9'
            title = '%s (%s on %s)' % (title, c['event_date_time'], name)
            title = title.replace('&amp;','&').replace('&quot;','"')
            cm_refresh = (Addon.get_string(30007), 
                      'XBMC.RunPlugin(%s/?mode=refresh)' % 
                           (Addon.plugin_url))
            cm_rec = (Addon.get_string(30008), 
                      'XBMC.RunPlugin(%s/?mode=record&rec=%s&set=%s&mt=%s)' % 
                           (Addon.plugin_url, urllib.quote(c['rec_url']),urllib.quote(c['set_url']),urllib.quote(c['mediatype'])))
            if Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'true':
                cm_menu = [cm_refresh, cm_rec]
            elif Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'false' and name in ['CW','ABC','FOX','PBS','CBS','NBC','My9']:
                cm_menu = [cm_refresh, cm_rec]
            else:
                cm_menu = [cm_refresh]
            Addon.add_list_item(c['title'],
            
                                 {'title': title,
                                 'plot': plot,
                                 'mediatype': mediatype,
                                 'tvshowtitle': tvshowtitle},
                                 img=poster_url, fanart=logo, playable=False, cm=cm_menu, cm_replace=True)
            xbmcplugin.setContent(Addon.plugin_handle, 'movie')

elif mode == 'sports_later':
    stream_type = 'rtmp'
    channels = ustv.get_sports(quality_type, stream_type, 'later')
    if channels:
        for c in channels:
            rURL = "plugin://plugin.video.ustvnow.tva/?name=" + c['name'] + "&mode=play"
            name = c["name"];
            logo = xbmc.translatePath(os.path.join(plugin_path, 'resources', 'images', c['name']+'.png'))
            poster_url = c["poster_url"];
            title = c["title"];
            plot = c["plot"].replace("&amp;", "&").replace('&quot;','"');
            mediatype = c["mediatype"];
            if mediatype != "movie":
                tvshowtitle = title
            if name == 'AE':
                name = 'A&E'
            if name == 'MY9':
                name = 'My9'
            title = '%s (%s on %s)' % (title, c['event_date_time'], name)
            title = title.replace('&amp;','&').replace('&quot;','"')
            cm_refresh = (Addon.get_string(30007), 
                      'XBMC.RunPlugin(%s/?mode=refresh)' % 
                           (Addon.plugin_url))
            cm_rec = (Addon.get_string(30008), 
                      'XBMC.RunPlugin(%s/?mode=record&rec=%s&set=%s&mt=%s)' % 
                           (Addon.plugin_url, urllib.quote(c['rec_url']),urllib.quote(c['set_url']),urllib.quote(c['mediatype'])))
            if Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'true':
                cm_menu = [cm_refresh, cm_rec]
            elif Addon.get_setting('rec_live') == 'true' and Addon.get_setting('dvr') == 'false' and name in ['CW','ABC','FOX','PBS','CBS','NBC','My9']:
                cm_menu = [cm_refresh, cm_rec]
            else:
                cm_menu = [cm_refresh]
            Addon.add_list_item(c['title'],
            
                                 {'title': title,
                                 'plot': plot,
                                 'mediatype': mediatype,
                                 'tvshowtitle': tvshowtitle},
                                 img=poster_url, fanart=logo, playable=False, cm=cm_menu, cm_replace=True)
            xbmcplugin.setContent(Addon.plugin_handle, 'movie')

elif mode == 'delete':
    ret = dlg.yesno(Addon.get_string(30000), Addon.get_string(30005))
    if ret == 1:
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        ustv.delete_recording(Addon.plugin_queries['del'])
        xbmc.executebuiltin('Container.Refresh')
        xbmc.executebuiltin("Dialog.Close(busydialog)")

elif mode == 'remove':
    ret = dlg.yesno(Addon.get_string(30000), Addon.get_string(30019))
    if ret == 1:
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        ustv.remove_recurring(Addon.plugin_queries['remove'])
        xbmc.executebuiltin('Container.Refresh')
        xbmc.executebuiltin("Dialog.Close(busydialog)")

elif mode == 'set':
    ret = dlg.yesno(Addon.get_string(30000), Addon.get_string(30023))
    if ret == 1:
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        ustv.set_recurring(Addon.plugin_queries['set'])
        xbmc.executebuiltin('Container.Refresh')
        xbmc.executebuiltin("Dialog.Close(busydialog)")

elif mode == 'record':
    ret = dlg.yesno(Addon.get_string(30000), Addon.get_string(30009))
    if ret == 1:
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        ustv.record_show(Addon.plugin_queries['rec'])
        if Addon.plugin_queries['mt'] != 'movie' and Addon.plugin_queries['mt'] != 'MV' and Addon.get_setting('dvr') == 'true':
            ret = dlg.yesno(Addon.get_string(30000), Addon.get_string(30027))
            if ret == 1:
                ustv.set_recurring(Addon.plugin_queries['set'])
                xbmc.executebuiltin("Dialog.Close(busydialog)")
            else:
                xbmc.executebuiltin("Dialog.Close(busydialog)")
    xbmc.executebuiltin('Container.Refresh')

elif mode == 'refresh':
    xbmc.executebuiltin('Container.Refresh')

elif mode == 'settings':
    Addon.show_settings()

elif mode=='play':
    name = Addon.plugin_queries['name']
    src = random.choice(['lv5', 'lv7', 'lv9'])
    Addon.log(name)
    stream_type = 'rtmp'
    channels = []
    channels = ustv.get_link(quality_type, stream_type, src)
    if channels:
        Addon.log(str(channels))
        for c in channels:
            if c['name'] == name:
                url = c['url']
                Addon.log(url)
                item = xbmcgui.ListItem(path=url)
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

Addon.end_of_directory()
