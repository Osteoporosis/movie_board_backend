sudo apt update
sudo apt upgrade --autoremove -y
sudo apt clean
sudo apt install python3-venv -y
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
