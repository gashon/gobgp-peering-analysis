import json
from collections import defaultdict

reserved_asn_ranges = [(64512, 65534), (4200000000, 4294967294)]  # Private ASN ranges
def is_private_asn(asn):
    return any(lower <= asn <= upper for lower, upper in reserved_asn_ranges)

asn_names = {}
with open("../data/as_names.txt") as f:
    for line in f:
        json_line = json.loads(line)

        asn = json_line['asn']
        name = json_line['name']

        asn_names[asn] = name

data = []
with open('../data/table.json', 'r') as file:
    for line in file:
        data.append(json.loads(line))

as_connectivity = defaultdict(lambda: {'appearances': 0, 'positions': 0})


for entry in data:
    if 'entries' in entry:
        for route_entry in entry['entries']:
            for attribute in route_entry['path_attributes']:
                if attribute['type'] == 2:  # AS_PATH attribute
                    # filter out private ASNs
                    as_path = [asn for asn in attribute['as_paths'][0]['asns'] if not is_private_asn(asn)]
                    # remove duplicated ASNs
                    as_path = list(dict.fromkeys(as_path))
                    for position, asn in enumerate(as_path, start=1):
                        as_connectivity[asn]['appearances'] += 1
                        as_connectivity[asn]['positions'] += position

# calculate connectivity score
for asn, metrics in as_connectivity.items():
    # Adjust the score calculation based on your analysis needs
    avg_position = metrics['positions'] / metrics['appearances']
    metrics['score'] = metrics['appearances'] / avg_position

# Rank ASes by Connectivity
sorted_as_connectivity = sorted(as_connectivity.items(), key=lambda x: x[1]['score'], reverse=True)

# Print the top 10 best connected ASes
for asn, metrics in sorted_as_connectivity[:10]:
    print(f"AS{asn} - {asn_names.get(asn, 'Unknown')}: {metrics['score']:.2f}")
