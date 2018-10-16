#!/usr/bin/python
##############################################################################
#
# A Python Implementation for create app instance to DCTG lib
#
# Copyright (C) 2018 Mellanox Technologies
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

import sys
import getopt
from random import randint
from xml.etree.ElementTree import Element, SubElement, Comment, ElementTree
from xml.etree import ElementTree as ET
from xml.dom import minidom
# import xml.etree.cElementTree as ET

class Gen(object):
    def __init__(self,role,addr,dataCenter,cluster,rack,host):
        self.role = role
        self.addr = addr
        self.dataCenter = dataCenter
        self.cluster = cluster
        self.rack = rack
        self.host = host

class AppType(object):
    def __init__(self, xmlPath):
        self.roles = list()
        self.xmlPath = xmlPath
        appTypeXml = ET.parse(xmlPath)
        root = appTypeXml.getroot()
        if root.attrib is None:
            raise Usage("wrong appType xml format AppType must have attribute (xml file: " + xmlPath + ")")
        self.name = root.attrib["Name"]
        for r in root.findall("Role"):
            if r.attrib is None:
                raise Usage("wrong appType xml format Role must have attribute (xml file: " + xmlPath + ")")
            self.roles.append(r.attrib["Name"])
class App(object):
    def __init__(self, appType,appName):
        self.gens = list()
        self.type = appType
        self.name = appName
    def CreateXml(self):
        if verbose:
            print "creating xml to app instance: %s " % self.name
        root = minidom.Document()
        appInst = root.createElement("AppInst")
        root.appendChild(appInst)
        # comment = Comment("This application-instance-xml generated by createAppInst.py")
        # appInst.append(comment)
        appType = root.createElement("AppType")
        appType.appendChild(root.createTextNode(self.type.xmlPath))
        appInst.appendChild(appType)
        # for g in self.gens:
        #     gen =  SubElement(appInst,"Gen")
        #     role = SubElement(gen,"Role")
        #     if g.role not in self.type.roles:
        #         raise Usage("-E- Role: " + g.role + " not in appType: " + self.type.name)
        #     role.text = g.role
        #     addr =  SubElement(gen,"Addr")
        #     addr.text = g.addr
        #     dataCenter =  SubElement(gen,"DC")
        #     dataCenter.text = str(g.dataCenter)
        #     cluster =  SubElement(gen,"Cluster")
        #     cluster.text = str(g.cluster)
        #     rack = SubElement(gen, "Rack")
        #     rack.text = str(g.rack)
        #     host = SubElement(gen,"Host")
        #     host.text = str(g.host)

        # xmlTree = ElementTree(appInst)
        # xmlTree.write("%s/%s.xml" % (outPath,self.name))
        self.WriteToXmlFile(root)

    def WriteToXmlFile(self,root):
        xmlFile = open("%s/%s.xml" % (outPath,self.name),'w')
        # rough_string = ET.tostring(elem)
        # reparsed = minidom.parseString(rough_string)
        # xmlFile.write(reparsed.toprettyxml(indent="\t"))
        xmlFile.write(root.toprettyxml(indent="\t"))
        xmlFile.close()

class TopoNode(object):
    def __init__(self, type,rolesAllowed):
        self.children = list()
        self.type = type
        self.rolesAllowed = rolesAllowed
        self.gensNum = 0
    def addChild(self,child):
        self.children.append(child)

class AppGen(object):
    appsVec = list()
    appTypesVec = list()
    addrParts = list()
    topology = TopoNode("Topo",[])
    def __init__(self, dataCenters,clusters,racks,hosts,appsVec,appTypesVec,addressPattern,minAppsSize,maxAppsSize,appsNamePrefix,iniPathPattern):
        for d in range(dataCenters):
            dataCenter = TopoNode("DC",[])
            for c in range(clusters):
                cluster = TopoNode("Cluster",[])
                for r in range(racks):
                    rack = TopoNode("Rack",[])
                    for h in range(hosts):
                        host = TopoNode("Host",[])
                        rack.addChild(host)
                    cluster.addChild(rack)
                dataCenter.addChild(cluster)
            self.topology.addChild(dataCenter)

        self.dataCenters = dataCenters
        self.clusters = clusters
        self.racks = racks
        self.hosts = hosts
        self.appsVec = appsVec
        self.appTypesVec = appTypesVec
        self.addressPattern = addressPattern
        self.addrParts = self.addressPattern.split("%")
        self.iniPathParts = iniPathPattern.split("%")
        self.minAppsSize = minAppsSize
        self.maxAppsSize = maxAppsSize
        self.appsNamePrefix = appsNamePrefix

    def run(self):
        iniFile = open("%s/DCTrafficGen.ini" % (outPath),'w')
        iniFile.write("######################################################\n")
        iniFile.write("# This ini config file generated by createAppInst.py #\n")
        iniFile.write("######################################################\n")
        iniFile.write("[Config DCTrafficGen]\n")
        curDataCenter = 0
        curCluster = 0
        curRack = 0
        curHost = 0
        i = 0
        # appVec[i] is the number of apps of type appTypesVec[i] we should generate
        for numOfApps in self.appsVec:
            appTypeXml = self.appTypesVec[i]
            appType = AppType(appTypeXml)
            # generate numOfApps applications of type appType
            for a in range(numOfApps):
                appSize = randint(self.minAppsSize,self.maxAppsSize)
                appName = self.appsNamePrefix + appType.name + str(a) + str(i)
                if verbose:
                    print "generate application of type %s and size" % appType.name, appSize
                    print "Roles:",appType.roles
                app = App(appType,appName)
                # generators to the app "appName"
                for gen in range(appSize):
                    host = self.topology.children[curDataCenter].children[curCluster].children[curRack].children[curHost]
                    addr = self.createStrByPattern(curDataCenter, curCluster, curRack, curHost, host.gensNum, self.addrParts)
                    roleNum = randint(0,len(appType.roles)-1)
                    role = appType.roles[roleNum]
                    gen = Gen(role,addr,curDataCenter,curCluster,curRack,curHost)
                    app.gens.append(gen)
                    iniPath = self.createStrByPattern(curDataCenter, curCluster, curRack, curHost, host.gensNum, self.iniPathParts)
                    iniFile.write("**.%s.appXmlConfig = \"%s/%s.xml\"\n" % (iniPath,outPath,appName))
                    # dataCenter.gensNum += 1
                    # cluster.gensNum += 1
                    # rack.gensNum += 1
                    host.gensNum += 1
                    curHost = (curHost + 1) % self.hosts
                    if curHost == 0:
                        curRack = (curRack + 1) % self.racks
                        if curRack == 0:
                            curCluster = (curCluster + 1) % self.clusters
                            if curCluster == 0:
                                curDataCenter = (curDataCenter + 1) % self.dataCenters

                app.CreateXml()
            i+=1
        iniFile.close()

    def createStrByPattern(self,dataCenter,cluster,rack,host,gen,patternParts):
        addr = patternParts[0]
        for i in range(1,len(patternParts)):
            firstChar = patternParts[i][0]
            num = 0
            if (firstChar == 'd'):
                num = dataCenter
            elif (firstChar == 'c'):
                num = cluster
            elif (firstChar == 'r'):
                num = rack
            elif (firstChar == 'h'):
                num = host
            elif (firstChar == 'g'):
                num = gen
            addr = addr + str(num) + patternParts[i][1:]
        return addr

    def getMostUnusedChild(self,topoNode):
        childUsage = list()
        for child in topoNode.children:
            childUsage.append(child.gensNum)
        mostUnusedChildNum = childUsage.index(min(childUsage))
        return topoNode.children[mostUnusedChildNum], mostUnusedChildNum

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

class SimFailure(Exception):
    def __init__(self, msg):
        self.msg = msg
        print "Fail to handle some Simulation condition: %s" % msg
verbose = False
def main(argv=None):
    global verbose
    global outPath
    outPath = "."
    addressPattern = "D%d-C%c-R%r-H%h-G%g"
    iniPathPattern = "dc[%d].cluster[%c].rack[%r].host[%h].gen[%g]"
    appsNamePrefix = "App"
    minAppsSize = 10
    maxAppsSize = 30
    dataCenters = 0
    clusters = 0
    racks = 0
    hosts = 0
    appsVec = list()
    appTypesVec = list()

    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:],
                                       "hvp:d:c:r:m:a:t:s:n:i:o:",
                                       ["help", "verbose", "address-pattern=",
                                        "data-centers=","clusters=", "racks=","hosts","apps","app-types","apps-size","apps-name","ini-pattern","out-path"])
        except getopt.error, msg:
             raise Usage(msg)
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print 'USAGE\ncreateAppInstances.py \n   -p|--address-pattern <pattern with %d,%c,%r,%h %g for dc,cluster,rack,host,gen numbers>\n   -d|--data-centers <num of dc>' \
                    '\n   -c|--clusters <num of clusters per dc>\n   -r|--racks <num of racks per cluster>\n   -m|--hosts <num of hosts per rack>\n   -a|--apps <num of apps per type separated by,>' \
                      '\n   -t|--app-types <app types separated by, (sould be the same number as --apps) \n   -s|--apps-size <min app size>,<max app size> ' \
                      '\n   -i|--ini-pattern <pattern to generator path in the ini file>\n   -o|--out-path <xml and ini output path>'
                print '\nDESCRIPTION: TBD\n' #TODO:
                sys.exit()
            elif opt in ("-p", "--address-pattern"):
                addressPattern = arg
            elif opt in ("-v", "--verbose"):
                verbose = True
            elif opt in ("-d", "--data-centers"):
                dataCenters = int(arg)
            elif opt in ("-c", "--clusters"):
                clusters = int(arg)
            elif opt in ("-r", "--racks"):
                racks = int(arg)
            elif opt in ("-m", "--hosts"):
                hosts = int(arg)
            elif opt in ("-n", "--apps-name"):
                appsNamePrefix = arg
            elif opt in ("-i", "--ini-pattern"):
                iniPathPattern = arg
            elif opt in ("-o", "--out-path"):
                outPath = arg
            elif opt in ("-s", "--apps-size"):
                mi,ma = arg.split(',')
                minAppsSize = int(mi)
                maxAppsSize = int(ma)
            elif opt in ("-a", "--apps"):
                for app in arg.split(','):
                    appsVec.append(int(app))
            elif opt in ("-t", "--app-types"):
                for appType in arg.split(','):
                    appTypesVec.append(appType)
        if verbose:
            print "-I- Parameters:" \
                  "Number of Data Centers: %d" % (dataCenters)
            print "Number of clusters: %d" % (clusters)
            print "Number of racks: %d" %(racks)
            print "Number of hosts: %d" %(hosts)
            i=0
            for a in appsVec:
                print "Generate %d apps of type %s" % (a,appTypesVec[i])
                i+=1
        if(len(appsVec)!= len(appTypesVec)):
            raise Usage("number of apps vector (len %d) should be correspond to app types (len %d)"%(len(appsVec),len(appTypesVec)))
        appGenerator = AppGen(dataCenters,clusters,racks,hosts,appsVec,appTypesVec,addressPattern,minAppsSize,
                              maxAppsSize,appsNamePrefix,iniPathPattern)
        appGenerator.run()

    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

    except SimFailure, err:
        print >>sys.stderr, "-F- " + err.msg
        return 3

if __name__ == "__main__":
    sys.exit(main())
