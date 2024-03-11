import json
import collections

paths = []
AS_list = set()

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

# Load paths and figure out all ASes:
with open('../data/table.json') as table:
  for line in table:
      d = json.loads(line)
      if "entries" in d:
        paths.append(d["entries"][0]["path_attributes"][1]["as_paths"][0]["asns"]) 
        path_ASes = set(d["entries"][0]["path_attributes"][1]["as_paths"][0]["asns"])
        AS_list.update(path_ASes)
        
peers = collections.defaultdict(set)

for path in paths:
    for index, AS in enumerate(path):
        # Make sure it's a public AS
        if not is_private_asn(AS):
            # Get left peer
            new_id = index
            if index != 0:
                while new_id > 0 and not is_private_asn(path[new_id]) and path[new_id] == AS:
                    new_id -= 1
            if new_id in range(len(path)) and path[new_id] not in peers[AS] and path[new_id] != AS and not is_private_asn(path[new_id]):
                peers[AS].add(path[new_id])
            
            # Get right peer
            new_id = index
            if index != len(path) - 1:
                while new_id < len(path) and not is_private_asn(path[new_id]) and path[new_id] == AS:
                    new_id += 1
            
            if new_id in range(len(path)) and path[new_id] not in peers[AS] and path[new_id] != AS and not is_private_asn(path[new_id]):
                peers[AS].add(path[new_id])

# Sort by number of peers from peers collection
peers_sorted = sorted(peers.items(), key=lambda x: len(x[1]), reverse=True)

# print top 10 most connected ASes
for i in range(10):
    print(f"{asn_names[peers_sorted[i][0]]} ({peers_sorted[i][0]}): {len(peers_sorted[i][1])} peers")

