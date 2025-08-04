import csv
import json
import re

# Paths
CSV_PATH = "../minecraft_1_8_1_color_table.csv"
COLOURSJSON_PATH = "../src/components/mapart/json/coloursJSON.json"
OUTPUT_PATH = "../src/components/mapart/json/coloursJSON_with_1_8.json"

def normalize_block_name(name):
    return re.sub(r'[^a-z0-9]', '', name.lower().replace('_', ''))

def find_nbt_for_block(block_name, coloursJSON):
    norm_name = normalize_block_name(block_name)
    for colourSet in coloursJSON.values():
        for block in colourSet["blocks"].values():
            displayName = block.get("displayName", "")
            if normalize_block_name(displayName) == norm_name:
                nbt = block.get("validVersions", {}).get("1.12.2")
                if isinstance(nbt, dict):
                    return {
                        "NBTName": nbt.get("NBTName", displayName),
                        "NBTArgs": nbt.get("NBTArgs", {}),
                    }
                else:
                    return {
                        "NBTName": displayName,
                        "NBTArgs": {},
                    }
    return {
        "NBTName": block_name,
        "NBTArgs": {},
    }

def main():
    with open(COLOURSJSON_PATH, "r") as f:
        coloursJSON = json.load(f)

    next_colourSetId = max(map(int, coloursJSON.keys())) + 1

    pending_sets = {}
    tone_order = ["unobtainable", "dark", "normal", "light"]

    with open(CSV_PATH, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            mapdatId = int(row["id"])
            rgb = [int(x) for x in row["rgb"].split(",")]
            blocks = [b.strip() for b in row["blocks"].split(",")]
            block_signature = tuple(sorted(b.lower() for b in blocks))

            if block_signature not in pending_sets:
                pending_sets[block_signature] = {
                    "mapdatId": mapdatId,
                    "blocks": blocks,
                    "tonesRGB": {},
                }

            tone_index = len(pending_sets[block_signature]["tonesRGB"])
            if tone_index >= 4:
                continue

            tone = tone_order[tone_index]
            pending_sets[block_signature]["tonesRGB"][tone] = rgb

    for block_signature, data in pending_sets.items():
        tonesRGB = data["tonesRGB"]
        blocks = data["blocks"]
        mapdatId = data["mapdatId"]

        for tone in tone_order:
            if tone not in tonesRGB:
                tonesRGB[tone] = [0, 0, 0]

        blocks_dict = {}
        for i, (block_name, tone) in enumerate(zip(blocks, tone_order)):
            nbt = find_nbt_for_block(block_name, coloursJSON)
            blocks_dict[str(i)] = {
                "displayName": f"1.8 {block_name}",
                "validVersions": {
                    "1.8": {
                        "NBTName": nbt["NBTName"],
                        "NBTArgs": nbt["NBTArgs"],
                    }
                },
                "supportBlockMandatory": False,
                "flammable": False,
                "presetIndex": i
            }

        colourSet = {
            "tonesRGB": tonesRGB,
            "blocks": blocks_dict,
            "mapdatId": mapdatId,
            "colourName": blocks[0] if blocks else f"Colour {mapdatId}",
        }

        coloursJSON[str(next_colourSetId)] = colourSet
        next_colourSetId += 1

    with open(OUTPUT_PATH, "w") as f:
        json.dump(coloursJSON, f, indent=4)

    print(f"Done. Output written to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()