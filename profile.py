#!/usr/bin/env python
import geni.portal as portal
import geni.rspec.pg as rspec
import geni.rspec.igext as IG
import geni.rspec.emulab.pnext as PN
import geni.urn as URN


tourDescription = """

# srsLTE Controlled RF

Use this profile to intantiate an end-to-end LTE network in a controlled RF
environment (wired connections between UE and eNB). The UE can be srsLTE-based
or a Nexus 5.

If you elect to use a Nexus 5, these nodes will be deployed:

* Nexus 5 (`rue1`)
* Generic Compute Node w/ ADB image (`adbnode`)
* Intel NUC5300/B210 w/ srsLTE eNB/EPC (`enb1`)

If instead you choose to use an srsLTE UE, these will be deployed:

* Intel NUC5300/B210 w/ srsLTE (`rue1`) or
* Intel NUC5300/B210 w/ srsLTE eNB/EPC (`enb1`)

"""

tourInstructions = """

### Start EPC and eNB

After your experiment becomes ready, login to `enb1` via `ssh` and do:

```
/local/repository/bin/start.sh
```

This will start a `tmux` session with three panes, running `srsepc` and
`srsenb`, and then leaving your cursor in the last pane. After you've associated
a UE with this eNB, you can use the third pane to run tests with `ping` or
`iperf`. If you are not familiar with `tmux`, it's a terminal multiplexer that
has some similarities to screen. Here's a [tmux cheat
sheet](https://tmuxcheatsheet.com), but `ctrl-b o` (move to other pane) and
`ctrl-b x` (kill pane), should get you pretty far. `ctrl-b d` will detach you
from the `tmux` session and leave it running in the background. You can reattach
with `tmux attach`.

If you'd like to start `srsepc` and `srsenb` manually, here are the commands:

```
# start srsepc
sudo srsepc /etc/srslte/epc.conf

# start srsenb
sudo srsenb /etc/srslte/enb.conf
```

### Nexus 5

If you've deployed a Nexus 5, you should see it sync with the eNB eventually and
obtain an IP address. Login to `adbnode` in order to access `rue1` via `adb`:

```
# on `adbnode`
pnadb -a
adb shell
```

Once you have an `adb` shell to `rue1`, you can use `ping` to test the
connection, e.g.,

```
# in adb shell connected to rue1
# ping SGi IP
ping 172.16.0.1
```

If the Nexus 5 fails to sync with the eNB, try rebooting it via the `adb` shell.
After reboot, you'll have to repeat the `pnadb -a` and `adb shell` commands on
`adbnode` to reestablish a connection to the Nexus 5.

### srsLTE UE

If you've deployed an srsLTE UE, login to `rue1` and do:

```
/local/repository/bin/start.sh
```

This will start a `tmux` session with two panes: one running srsue and the other
holding a spare terminal for running tests with `ping` and `iperf`. Again, if
you'd like to run `srsue` manually, do:

```
sudo srsue /etc/srslte/ue.conf
```

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
rflink1 = request.RFLink1("rflink1")
rflink1.addInterface(enb1_ue_rf)
rflink1.addInterface(ue_enb1_rf)

rflink2 = request.RFLink2("rflink2")
rflink2.addInterface(enb2_ue_rf)
rflink2.addInterface(ue_enb2_rf)

tour = IG.Tour()
tour.Description(IG.Tour.MARKDOWN, tourDescription)
tour.Instructions(IG.Tour.MARKDOWN, tourInstructions)
request.addTour(tour)

pc.printRequestRSpec(request)
