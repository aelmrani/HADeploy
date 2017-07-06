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

from ansible.inventory import Inventory
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager

from hadeploy.core.plugin import Plugin
from hadeploy.core.const import SRC

HOSTS="hosts"
HOST_GROUPS="host_groups"
NAME="name"
SSH_PRIVATE_FILE_FILE="ssh_private_key_file"
GROUPS="groups"
ANSIBLE_INVENTORY_FILE="ansible_inventory_files"
VAULT_PASSWORD_FILE="ansible_vault_password_file"

logger = logging.getLogger("hadeploy.plugins.ansible")

class AnsiblePlugin(Plugin):
    
    def __init__(self, name, path, context):
        Plugin.__init__(self, name, path, context)


    def onNewSnippet(self, snippetPath):
        if ANSIBLE_INVENTORY_FILE in self.context.model[SRC]:
            l2 = []
            for p in self.context.model[SRC][ANSIBLE_INVENTORY_FILE]:
                if isinstance(p, basestring):
                    l2.append(misc.snippetRelocate(snippetPath, p))
                else:
                    misc.ERROR("ansible_inventory_files must be a list of string!")
            self.context.model[SRC][ANSIBLE_INVENTORY_FILE] = l2
            if VAULT_PASSWORD_FILE in self.context.model[SRC]:
                self.context.model[SRC][VAULT_PASSWORD_FILE] = misc.snippetRelocate(snippetPath, self.context.model[SRC][VAULT_PASSWORD_FILE])

    def getGroomingPriority(self):
        return 1300
    
    def onGrooming(self):
        if ANSIBLE_INVENTORY_FILE in self.context.model[SRC]:
            print "\n****** WARNING: The definition 'ansible_inventory_files' is deprecated. Please use 'ansible_inventories' instead\n"
            for inventoryFile in self.context.model[SRC][ANSIBLE_INVENTORY_FILE]:
                if not os.path.exists(inventoryFile):
                    misc.ERROR("Ansible inventory file '{0}' does not exists!".format(inventoryFile))
                else:
                    populateModelFromInventory(self.context.model[SRC], inventoryFile)


def populateModelFromInventory(model, inventoryFile):
    loader = DataLoader()
    if VAULT_PASSWORD_FILE in model:
        vpf = model[VAULT_PASSWORD_FILE]
        if not os.path.exists(vpf):
            misc.ERROR("Ansible vault password file '{0}' does not exists!".format(vpf))
        with open(vpf) as f:
            content = f.readlines()
        if len(content) == 0 or len(content[0].strip()) == 0:
            misc.ERROR("Invalid Ansible vault password file '{0}' content!".format(vpf))
        loader.set_vault_password(content[0].strip())
    variable_manager = VariableManager()
    
    if HOSTS not in model:
        model[HOSTS] = []
    if HOST_GROUPS not in model:
        model[HOST_GROUPS] = []
    
    try:
        inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=inventoryFile)
    except Exception as e:
        misc.ERROR(str(e))
    
    variable_manager.set_inventory(inventory)
    
    hosts = inventory.get_hosts()
    
    existingHosts = set(map(lambda x : x[NAME], model[HOSTS]))
    #print(existingHosts)
    for host in hosts:
        if not host.name in existingHosts:
            h = {}
            h[NAME] = host.name.encode('utf8')
            for key in host.vars:
                if key.startswith('ansible_'):
                    key2 = key[len('ansible_'):].encode('utf8')
                    h[key2] = host.vars[key].encode('utf8')
                    # ssh_private_key_file may be relative to source inventory file. Set it absolute
                    if key2 == SSH_PRIVATE_FILE_FILE:
                        p = h[key2]
                        if not os.path.isabs(p):
                            h[key2] = os.path.normpath(os.path.join(os.path.dirname(inventoryFile), p))
            model[HOSTS].append(h)

    existingHostGroups = set(map(lambda x : x[NAME], model[HOST_GROUPS]))
    #print(existingHostGroups)
    hvars = variable_manager.get_vars(loader, host=hosts[0], include_hostvars=False)
    groups = hvars[GROUPS]
    for grpName in groups:
        if grpName != 'all' and grpName != 'ungrouped' and (not grpName in existingHostGroups):
            grp = {}
            grp[NAME] = grpName.encode('utf8')
            l = []
            for h in groups[grpName]:
                l.append(h.encode('utf8')) 
            grp[HOSTS] = l
            model[HOST_GROUPS].append(grp)
            
            
    