# Copyright (C) 2017 BROADSoftware
#
# This file is part of HADeploy
#
# HADeploy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# HADeploy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with HADeploy.  If not, see <http://www.gnu.org/licenses/>.

import logging
import hadeploy.core.misc as misc
import os
from hadeploy.core.plugin import Plugin
from hadeploy.core.const import SRC,DATA,SCOPE_SYSTEMD,ACTION_DEPLOY,ACTION_REMOVE
from hadeploy.plugins.files.code import lookupInLocalFiles,lookupInLocalTemplates
from sets import Set

logger = logging.getLogger("hadeploy.plugins.systemd")

SYSTEMD_UNITS="systemd_units"
NAME="name"
SCOPE="scope"
UNIT_FILE="unit_file"
USER="user"
NO_REMOVE="no_remove"
_UNIT_FILE_="_unit_file_"


SYSTEMD="systemd"
SCOPE_BY_NAME="scopeByName"     

_SRC_="_src_"
_DISPLAY_SRC_="_displaySrc_"

ENABLED="enabled"
STATE="state"
ST_STARTED="started"
ST_STOPPED="stopped"
ST_CURRENT="current"

ACTION_ON_NOTIFY="action_on_notify"
AON_RESTART="restart"
AON_RELOAD="reload"
AON_NONE="none"

validState= Set([ST_STARTED, ST_STOPPED, ST_CURRENT])
validAon = Set([AON_NONE, AON_RELOAD, AON_RESTART])




class FilesPlugin(Plugin):
    
    def __init__(self, name, path, context):
        Plugin.__init__(self, name, path, context)

           
    def getGroomingPriority(self):
        return 3200     

    def getSupportedScopes(self):
        return [SCOPE_SYSTEMD]        
 
    def getSupportedActions(self):
        return [ACTION_DEPLOY, ACTION_REMOVE]

    def getPriority(self, action):
        return 3200 if action == ACTION_DEPLOY else 3800 if action == ACTION_REMOVE else misc.ERROR("Plugin 'systemd' called with invalid action: '{0}'".format(action))

    def onGrooming(self):
        if self.context.toExclude(SCOPE_SYSTEMD):
            return
        model = self.context.model
        misc.ensureObjectInMaps(model[DATA], [SYSTEMD, SCOPE_BY_NAME], {})
        if SYSTEMD_UNITS in model[SRC]:
            for unit in model[SRC][SYSTEMD_UNITS]:
                misc.setDefaultInMap(unit, NO_REMOVE, False)
                misc.setDefaultInMap(unit, ENABLED, True)
                misc.setDefaultInMap(unit, STATE, ST_CURRENT)
                if unit[STATE] not in validState:
                    misc.ERROR("Systemd_unit {0}: state value '{1}' is not valid. Must be one of {2}".format(unit[NAME], unit[STATE], validState))
                misc.setDefaultInMap(unit, ACTION_ON_NOTIFY, AON_RESTART)
                if unit[ACTION_ON_NOTIFY] not in validAon:
                    misc.ERROR("Systemd_unit {0}: action_on_notify value '{1}' is not valid. Must be one of {2}".format(unit[NAME], unit[ACTION_ON_NOTIFY], validAon))
                if not self.context.checkScope(unit[SCOPE]):
                    misc.ERROR("Systemd_unit {0}: scope attribute '{1}' does not match any host or host_group!".format(unit[NAME], unit[SCOPE]))
                else:
                    if not unit[SCOPE] in  self.context.model[DATA][SYSTEMD][SCOPE_BY_NAME]:
                        self.context.model[DATA][SYSTEMD][SCOPE_BY_NAME][unit[SCOPE]] = []
                    self.context.model[DATA][SYSTEMD][SCOPE_BY_NAME][unit[SCOPE]].append(unit)
                if unit[UNIT_FILE].startswith("file://"):
                    path = unit[UNIT_FILE][len('file://'):] 
                    unit[_DISPLAY_SRC_] = path
                    if not path.startswith("/"):
                        path = lookupInLocalFiles(path, model)
                    else:
                        if not os.path.exists(path):
                            misc.ERROR("'{0}' does not exists".format(path))
                    if os.path.isdir(path):
                        misc.ERROR("Unit_file '{0}' can't be a folder!".format(unit[UNIT_FILE]))
                    unit[_UNIT_FILE_] = path                    
                elif unit[UNIT_FILE].startswith("tmpl://"):
                    path = unit[UNIT_FILE][len('tmpl://'):] 
                    unit[_DISPLAY_SRC_] = path
                    if not path.startswith("/"):
                        path = lookupInLocalTemplates(path, model)
                    else:
                        if not os.path.exists(path):
                            misc.ERROR("'{0}' does not exists".format(path))
                    if os.path.isdir(path):
                        misc.ERROR("Unit_file '{0}' can't be a folder!".format(unit[UNIT_FILE]))
                    unit[_UNIT_FILE_] = path                    
                else:
                    misc.ERROR("Systemd_unit '{0}': {1} is not a valid form for 'unit_file' attribute. Unknown scheme.".format(unit[NAME], unit[UNIT_FILE]))
                    

