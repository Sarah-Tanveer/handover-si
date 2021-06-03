#!/usr/bin/env python
import os
import geni.portal as portal
import geni.rspec.pg as rspec
import geni.rspec.igext as IG
import geni.rspec.emulab.pnext as PN
import geni.urn as URN


tourDescription = """
## srsRAN Handover

"""

tourInstructions = """

"""

BIN_PATH = "/local/repository/bin"
DEPLOY_SRS = os.path.join(BIN_PATH, "deploy-srs.sh")
DEPLOY_OPEN5GS = os.path.join(BIN_PATH, "deploy-open5gs.sh")
TUNE_CPU = os.path.join(BIN_PATH, "tune-cpu.sh")
NUC_HWTYPE = "nuc5300"
UBUNTU_1804_IMG = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU18-64-STD"
SRSLTE_IMG = "urn:publicid:IDN+emulab.net+image+PowderProfiles:U18LL-SRSLTE"


pc = portal.Context()
node_type = [
    ("d740",
     "Emulab, d740"),
    ("d430",
     "Emulab, d430")
]

pc.defineParameter("cn_node_type",
                   "Type of compute node for Open5GS CN",
                   portal.ParameterType.STRING,
                   node_type[0],
                   node_type)

pc.defineParameter("enb1_node", "PhantomNet NUC+B210 for first eNodeB",
                   portal.ParameterType.STRING, "", advanced=True,
                   longDescription="Specific eNodeB node to bind to.")

pc.defineParameter("enb2_node", "PhantomNet NUC+B210 for second eNodeB",
                   portal.ParameterType.STRING, "", advanced=True,
                   longDescription="Specific eNodeB node to bind to.")

pc.defineParameter("ue_node", "PhantomNet NUC+B210 for UE",
                   portal.ParameterType.STRING, "", advanced=True,
                   longDescription="Specific UE node to bind to.")

params = pc.bindParameters()
pc.verifyParameters()
request = pc.makeRequestRSpec()

cn = request.RawPC("cn")
cn.hardware_type = params.cn_node_type
cn.disk_image = UBUNTU_1804_IMG
cn.addService(rspec.Execute(shell="bash", command=DEPLOY_OPEN5GS))
cn_s1_if = cn.addInterface("cn_s1_if")
cn_s1_if.addAddress(rspec.IPv4Address("192.168.1.1", "255.255.255.0"))
cn_link = request.Link("cn_link")
cn_link.addInterface(cn_s1_if)

ue = request.RawPC("ue")
ue.hardware_type = NUC_HWTYPE
ue.component_id = params.ue_node
ue.disk_image = SRSLTE_IMG
ue.Desire("rf-controlled", 1)
ue_enb1_rf = ue.addInterface("ue_enb1_rf")
ue_enb2_rf = ue.addInterface("ue_enb2_rf")
ue.addService(rspec.Execute(shell="bash", command=DEPLOY_SRS))
ue.addService(rspec.Execute(shell="bash", command=TUNE_CPU))

enb1 = request.RawPC("enb1")
enb1.hardware_type = NUC_HWTYPE
enb1.component_id = params.enb1_node
enb1.disk_image = SRSLTE_IMG
enb1_s1_if = enb1.addInterface("enb1_s1_if")
enb1_s1_if.addAddress(rspec.IPv4Address("192.168.1.2", "255.255.255.0"))
enb1.Desire("rf-controlled", 1)
enb1_ue_rf = enb1.addInterface("enb1_ue_rf")
enb1.addService(rspec.Execute(shell="bash", command=DEPLOY_SRS))
enb1.addService(rspec.Execute(shell="bash", command=TUNE_CPU))

enb2 = request.RawPC("enb2")
enb2.hardware_type = NUC_HWTYPE
enb2.component_id = params.enb2_node
enb2.disk_image = SRSLTE_IMG
enb2_s1_if = enb1.addInterface("enb2_s1_if")
enb2_s1_if.addAddress(rspec.IPv4Address("192.168.1.3", "255.255.255.0"))
enb2.Desire("rf-controlled", 1)
enb2_ue_rf = enb2.addInterface("enb2_ue_rf")
enb2.addService(rspec.Execute(shell="bash", command=DEPLOY_SRS))
enb2.addService(rspec.Execute(shell="bash", command=TUNE_CPU))

# Create S1 links between eNodeBs and CN
link = request.LAN("lan")
link.addInterface(cn_s1_if)
link.addInterface(enb1_s1_if)
link.addInterface(enb2_s1_if)
link.link_multiplexing = True
link.vlan_tagging = True
link.best_effort = True

# Create RF links between the UE and eNodeBs
rflink1 = request.RFLink("rflink1")
rflink1.addInterface(enb1_ue_rf)
rflink1.addInterface(ue_enb1_rf)

rflink2 = request.RFLink("rflink2")
rflink2.addInterface(enb2_ue_rf)
rflink2.addInterface(ue_enb2_rf)

tour = IG.Tour()
tour.Description(IG.Tour.MARKDOWN, tourDescription)
tour.Instructions(IG.Tour.MARKDOWN, tourInstructions)
request.addTour(tour)

pc.printRequestRSpec(request)
