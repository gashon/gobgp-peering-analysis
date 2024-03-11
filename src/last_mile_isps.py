import json
from ipaddress import ip_network, collapse_addresses

# Load ASN names
asn_names = {}
with open('../data/as_names.txt') as f:
    for line in f:
        json_line = json.loads(line)
        asn = json_line['asn']
        name = json_line['name']
        asn_names[asn] = name

prefix_count_by_asn = {}
ip_count_by_asn = {}
transit_asns = set()
prefixes_by_asn = {}  # New dictionary to collect prefixes

def ip_addresses_in_prefix(prefix):
    return ip_network(prefix).num_addresses

with open("../data/table.json", "r") as file:
    for line in file:
        entry = json.loads(line)
        if 'prefix' in entry and 'entries' in entry and entry['entries']:
            prefix = entry['prefix']['prefix']
            as_path = None
            # Extract AS path from path attributes
            for attr in entry['entries'][0]['path_attributes']:
                if attr['type'] == 2:  # AS_PATH
                    as_path = attr['as_paths'][0]['asns']
                    break
            
            # Ignore if AS_PATH is empty
            if not as_path:
                continue
            
            last_asn = as_path[-1]
            
            # Collect prefixes for each AS
            if last_asn not in prefixes_by_asn:
                prefixes_by_asn[last_asn] = []
            prefixes_by_asn[last_asn].append(prefix)
            
            # Track transit ASNs
            if len(as_path) > 1:
                for asn in as_path[:-1]:
                    transit_asns.add(asn)

# Coalesce prefixes and update counts
for asn, prefixes in prefixes_by_asn.items():
    coalesced_prefixes = list(collapse_addresses([ip_network(p) for p in prefixes]))  # Convert generator to list
    ip_count = sum(ip_addresses_in_prefix(p.with_prefixlen) for p in coalesced_prefixes)
    
    prefix_count_by_asn[asn] = len(coalesced_prefixes)  
    ip_count_by_asn[asn] = ip_count

# Exclude transit ASNs to identify last mile ISPs
last_mile_asns = set(prefix_count_by_asn.keys()) - transit_asns

# Sort and display results
N = 10
print("Top", N, "Last Mile ISPs by Number of Advertised Prefixes:")
sorted_isps_by_prefix = sorted([(asn, prefix_count_by_asn[asn], ip_count_by_asn[asn]) for asn in last_mile_asns], key=lambda x: (-x[1], -x[2]))
for asn, prefix_count, ip_count in sorted_isps_by_prefix[:N]:
    print(asn_names.get(asn, asn), prefix_count, 'prefixes', ip_count, 'IP addresses')

print("\nTop", N, "Last Mile ISPs by Number of IP Addresses:")
sorted_isps_by_ip_count = sorted([(asn, ip_count_by_asn[asn], prefix_count_by_asn[asn]) for asn in last_mile_asns], key=lambda x: -x[1])
for asn, ip_count, prefix_count in sorted_isps_by_ip_count[:N]:
    print(asn_names.get(asn, asn), ip_count, 'IP addresses', prefix_count, 'prefixes')

