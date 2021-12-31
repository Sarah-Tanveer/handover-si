set -ex
BINDIR=`dirname $0`
source $BINDIR/common.sh

if [ -f $SRCDIR/open5gs-setup-complete ]; then
    echo "setup already ran; not running again"
    exit 0
fi

sudo apt update
sudo apt install -y software-properties-common
# sudo add-apt-repository -y ppa:open5gs/latest

sudo apt install mongodb
sudo systemctl start mongodb 
sudo systemctl enable mongodb
sudo ip tuntap add name ogstun mode tun
echo "here1"
sudo ip addr add 10.45.0.1/16 dev ogstun
echo "here2"
sudo ip addr add 2001:230:cafe::1/48 dev ogstun
echo "here3"
sudo ip link set ogstun up
sudo apt install python3-pip python3-setuptools python3-wheel ninja-build build-essential flex bison git libsctp-dev libgnutls28-dev libgcrypt-dev libssl-dev libidn11-dev libmongoc-dev libbson-dev libyaml-dev libnghttp2-dev libmicrohttpd-dev libcurl4-gnutls-dev libnghttp2-dev libtins-dev meson
echo "here4"
git clone https://github.com/Sarah-Tanveer/open5gs
echo "here5"
cd open5gs
echo "here6"
meson build --prefix=`pwd`/install
echo "here7"
ninja -C build
./build/tests/attach/attach ## EPC Only
echo "here8"
./build/tests/registration/registration ## 5G Core Only
echo "here9"
cd build
meson test -v
echo "here10"
cd build
ninja install
echo "here11"
cd ../

echo "here12"
sudo apt install -y open5gs
sudo cp /local/repository/etc/open5gs/* /etc/open5gs/
sudo systemctl restart open5gs-mmed
sudo systemctl restart open5gs-sgwud

#TODO: find a better method for adding subscriber info
cd $SRCDIR
wget https://raw.githubusercontent.com/open5gs/open5gs/main/misc/db/open5gs-dbctl
chmod +x open5gs-dbctl
./open5gs-dbctl add 001010123456789 00112233445566778899aabbccddeeff 63BFA50EE6523365FF14C1F45F88737D  # IMSI,K,OPC
./open5gs-dbctl type 001010123456789 1  # APN type IPV4
touch $SRCDIR/open5gs-setup-complete
