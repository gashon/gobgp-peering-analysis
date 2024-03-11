import json

OUTPUT_FILE = "../data/output/public_peerings.txt"

import json

reserved_asn_ranges = [(64512, 65534), (4200000000, 4294967294)]  # Private ASN ranges
def is_private_asn(asn):
    return any(lower <= asn <= upper for lower, upper in reserved_asn_ranges)

# Load ASN names to identify public peers
public_asns = set()
with open('../data/as_names.txt') as f:
    for line in f:
        json_line = json.loads(line)

        asn = json_line['asn']
        if not is_private_asn(asn):
            public_asns.add(asn)

public_peerings = set()
# Load routing table
with open('../data/table.json', 'r') as f:
    for line in f:
        route = json.loads(line)

        if 'entries' in route:
            for entry in route['entries']:
                for attribute in entry['path_attributes']:
                    if attribute['type'] == 2:  # AS_PATH attribute
                        asns = [asn for segment in attribute['as_paths'] for asn in segment['asns']]
                        for asn in asns:
                            if not is_private_asn(asn):  # Assuming public ASNs are listed in as_names.txt
                                public_peerings.add(asn)

print(f"Number of public peerings identified: {len(public_peerings)}")
# compare with the number of ASNs in as_names.txt
print(f"Number of public asns in as_names.txt: {len(public_asns)}")

# print some 
# for asn in list(public_peerings)[:10]:
#     print(f"ASN: {asn}, Name: {asn_names.get(asn, 'Unknown')}")
#
print(f"writing to {OUTPUT_FILE}")
with open(OUTPUT_FILE, 'w') as output_file:
    json.dump(list(public_peerings), output_file)
    
