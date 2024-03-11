import json
from ipaddress import ip_network, summarize_address_range

reserved_asn_ranges = [(64512, 65534), (4200000000, 4294967294)]  # Private ASN ranges

def is_private_asn(asn):
    return any(lower <= asn <= upper for lower, upper in reserved_asn_ranges)
    
def load_asn_names(filename):
    asn_names = {}
    with open(filename) as f:
        for line in f:
            json_line = json.loads(line)
            asn = json_line['asn']
            name = json_line['name']
            asn_names[asn] = name
    return asn_names

def load_json(filename):
    res = [] 
    with open(filename, 'r') as file:
        for line in file:
            res.append(json.loads(line))
    return res

def coalesce_prefixes(prefixes):
    # Convert string prefixes to ip_network objects and sort
    networks = sorted([ip_network(prefix) for prefix in prefixes], key=lambda x: x.prefixlen)
    coalesced = ip_network('0.0.0.0/0').address_exclude(networks[0])  # Initialize with an inverse to start coalescing
    for network in networks:
        new_coalesced = []
        for coalesced_network in coalesced:
            if network.overlaps(coalesced_network):
                new_coalesced.extend(list(coalesced_network.address_exclude(network)))
            else:
                new_coalesced.append(coalesced_network)
        coalesced = new_coalesced
    return [net.with_prefixlen for net in coalesced if net.prefixlen != 0]  # Exclude the dummy initialization

def analyze_isps(data):
    prefixes_per_as = {}
    for entry in data:
        if 'prefix' in entry:
            prefix = entry['prefix']['prefix']
            if 'entries' in entry:
                for attr in entry['entries'][0]['path_attributes']:
                    if attr['type'] == 2:  # AS_PATH
                        as_path = attr['as_paths'][0]['asns']
                        origin_as = as_path[-1]  # Consider origin AS
                        if not is_private_asn(origin_as):
                            if origin_as not in prefixes_per_as:
                                prefixes_per_as[origin_as] = []
                            prefixes_per_as[origin_as].append(prefix)
                        break
    
    ip_count_per_as = {}
    for asn, prefixes in prefixes_per_as.items():
        coalesced_prefixes = coalesce_prefixes(prefixes)
        ip_count = sum(ip_network(prefix).num_addresses for prefix in coalesced_prefixes)
        ip_count_per_as[asn] = ip_count
    return ip_count_per_as

# Load the ASN names and table data
asn_names = load_asn_names('../data/as_names.txt')
table_data = load_json('../data/table.json')

# Analyze ISPs
ip_count_per_as = analyze_isps(table_data)

# Sort ASes by IP count and print top ISPs
sorted_as_ip_counts = sorted(ip_count_per_as.items(), key=lambda x: x[1], reverse=True)

for asn, count in sorted_as_ip_counts[:10]:
    print(f"{asn_names.get(asn, 'AS'+str(asn))}: {count} IPs")

