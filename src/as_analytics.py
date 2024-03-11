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

# Function to load JSON data
def load_json(filename):
    res =[] 

    with open(filename, 'r') as file:
        for l in file:
            res.append(json.loads(l))

    return res

def ip_addresses_in_prefix(prefix):
    _, prefix_length = prefix.split('/')
    return 2 ** (32 - int(prefix_length))

def coalesce_prefixes(prefixes):
    # Convert string prefixes to ip_network objects
    networks = [ip_network(prefix) for prefix in prefixes]
    # Sort networks by size (smaller to larger) to facilitate merging
    networks.sort(key=lambda net: net.prefixlen, reverse=True)
    # Use summarize_address_range to coalesce adjacent or overlapping networks
    coalesced = []
    while networks:
        # Take the first network as the start of a new range
        current = networks.pop(0)
        for other in list(networks):
            # Attempt to summarize current and other
            try:
                summarized = list(summarize_address_range(current[0], other[-1]))
                if len(summarized) == 1:
                    # If successful, set current to the summarized range and remove the other network
                    current = summarized[0]
                    networks.remove(other)
            except ValueError:
                # If the range cannot be summarized, move on
                continue
        coalesced.append(current)
    return [net.with_prefixlen for net in coalesced]

def analyze_ases(data):
    all_ases = set()
    origin_ases = {}
    origin_ases_prefixes = {}  # Track prefixes for coalescing
    for entry in data:
        if 'entries' in entry and entry['entries'] and 'prefix' in entry:
            prefix = entry['prefix']['prefix']
            for path_attribute in entry['entries'][0]['path_attributes']:
                if path_attribute['type'] == 2:  # AS_PATH attribute
                    as_path = path_attribute['as_paths'][0]['asns']
                    for as_ in as_path:
                        # Skip private ASNs
                        if not is_private_asn(as_):
                            all_ases.add(as_)

                    # Collect prefixes for origin AS
                    origin_as = as_path[-1]
                    if origin_as not in origin_ases_prefixes:
                        origin_ases_prefixes[origin_as] = []
                    origin_ases_prefixes[origin_as].append(prefix)

    # Coalesce and count IP addresses for origin ASes
    origin_ases_ip_count = {}
    for origin_as, prefixes in origin_ases_prefixes.items():
        coalesced_prefixes = coalesce_prefixes(prefixes)
        ip_count = sum(ip_addresses_in_prefix(prefix) for prefix in coalesced_prefixes)
        origin_ases_ip_count[origin_as] = ip_count
        origin_ases[origin_as] = len(coalesced_prefixes)

    # ases that only transit traffic
    transit_only_ases = all_ases - set(origin_ases.keys())

    return all_ases, origin_ases_ip_count, origin_ases, transit_only_ases

# Function to find top 10 ASes by number of originated prefixes
def top_10_origin_ases(origin_ases):
    return sorted(origin_ases.items(), key=lambda x: x[1], reverse=True)[:10]

asn_names = load_asn_names('../data/as_names.txt')
table_data = load_json('../data/table.json')

all_ases, origin_ases_ip_count, origin_ases, transit_only_ases = analyze_ases(table_data)

# map transit only ASes to their names
transit_only_as_names = {as_num: asn_names.get(as_num, "Name not found") for as_num in transit_only_ases}

top_10_origins = top_10_origin_ases(origin_ases)

# print stats
print(f"Total ASes: {len(all_ases)}")
print(f"ASes originating routes: {len(origin_ases)}")

print("\n\nTop 10 ASes by number of originated prefixes:")
for as_, count in top_10_origins:
    name = asn_names.get(as_, "Name not found")
    print(f"AS{as_}: {name} - {count} prefixes")

print("\n\nTop 10 ASes by ip count:", len(transit_only_ases))
top_10_origin_ip_count = sorted(origin_ases_ip_count.items(), key=lambda x: x[1], reverse=True)[:10]
for as_, count in top_10_origin_ip_count:
    name = asn_names.get(as_, "Name not found")
    print(f"AS{as_}: {name} - {count} IPs")


print("\n\nTransit only ASes:")
for as_, name in transit_only_as_names.items():
    print(f"AS{as_}: {name}")


