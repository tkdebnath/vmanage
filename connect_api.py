import requests
from ipaddress import ip_address
from netaddr import IPAddress
import pandas as pd
from creds import username, password
from creds import vmanage_url as vmanage_base_url
from pathlib import Path
requests.packages.urllib3.disable_warnings()

def main():

    # Login to vManage and get the session token
    login_url = f"{vmanage_base_url}/j_security_check"
    login_data = {
        "j_username": username,
        "j_password": password,
    }
    session = requests.Session()
    session.post(login_url, data=login_data, verify=False)

    # Get the list of devices
    devices_url = f"{vmanage_base_url}/dataservice/device"
    response = session.get(devices_url)

    if response.status_code == 200:
        devices_data = response.json()
        
        # Iterate through devices
        for device in devices_data["data"]:
            device_id = device["deviceId"]
            device_name = device["host-name"]
            device_type = device["device-type"]
            
            
            
            if device_type not in ["vmanage" , "vsmart", "vbond", "AP-vedge"]:
                # Fetch interfaces for the device
                interfaces_url = f"{vmanage_base_url}/dataservice/device/interface?deviceId={device_id}"
                interfaces_response = session.get(interfaces_url)
                #ipdb.set_trace()
                
                if interfaces_response.status_code == 200:
                    interfaces_data = interfaces_response.json()
                    
                    # Iterate through interfaces and print their IP addresses and CIDR
                    for interface in interfaces_data["data"]:
                        try:
                            if interface['ip-address'] != "0.0.0.0" and interface['ipv4-subnet-mask'] != "0.0.0.0" and "Tunnel" not in interface["ifname"]:
                                interface_name = interface["ifname"]
                                ip_addr = interface["ip-address"]
                                prefix_length = interface["ipv4-subnet-mask"]
                                cidr = IPAddress(prefix_length).netmask_bits()
                                if not ip_address(ip_addr).is_private:
                                    print(f"Device: {device_name}, IP Address: {ip_addr}/{cidr}")
                                    dict_db.append({"Device": device_name, "IP Address": f"{ip_addr}/{cidr}"})
                        except KeyError:
                            continue
                else:
                    print(f"Failed to fetch interfaces for device {device_name}. Status Code: {interfaces_response.status_code}")
                    failed_db.append({"Device": device_name, "IP Address": f"Failed"})
    else:
        print(f"Failed to fetch devices. Status Code: {response.status_code}")

if __name__=='__main__':
    dict_db = []
    failed_db = []
    
    main()
    
    directory = "/mnt/data/file_server_storage/wan_ip"
    Path.mkdir(directory, exist_ok=True)
    
    if len(dict_db) > 0:
        with open(file=f"{directory}/WAN_IPs.txt", mode="w", encoding="utf-8") as fp:
            for item in dict_db:
                fp.write(f"{item['IP Address']}\n")
    if len(failed_db) > 0:
        df = pd.DataFrame(failed_db)
        df.to_csv(f"{directory}/Failed_cEdges.txt", index=False, encoding="utf-8")