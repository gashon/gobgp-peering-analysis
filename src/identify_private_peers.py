import json

OUTPUT_FILE = "../data/output/private_peerings.json"

import json


reserved_asn_ranges = [(64512, 65534), (4200000000, 4294967294)]  # Private ASN ranges
def is_private_asn(asn):
    return any(lower <= asn <= upper for lower, upper in reserved_asn_ranges)

private_asns = set()
with open('../data/as_names.txt') as f:
    for line in f:
        json_line = json.loads(line)
        asn = json_line['asn']

        if is_private_asn(asn):
            private_asns.add(asn)

private_peerings = set()
with open('../data/table.json') as f:
    for line in f:
        route = json.loads(line)
        if 'entries' in route:
            for entry in route['entries']:
                for attribute in entry['path_attributes']:
                    if attribute['type'] == 2:  # AS_PATH attribute
                        asns = [asn for segment in attribute['as_paths'] for asn in segment['asns']]
                        for asn in asns:
                            if any(lower <= asn <= upper for lower, upper in reserved_asn_ranges):
                                private_peerings.add(asn)

print(f"Number of private peerings identified: {len(private_peerings)}")
# compare with the number of ASNs in as_names.txt
print(f"Number of private asns in as_names.txt: {len(private_asns)}")

print(f"writing to {OUTPUT_FILE}")
with open(OUTPUT_FILE, 'w') as output_file:
    json.dump(list(private_peerings), output_file)
    
