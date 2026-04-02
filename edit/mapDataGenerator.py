import amulet
import os
import json
import math
import numpy as np
from PIL import Image

def get_map_color(block_name):
    block_name = block_name.lower().replace("minecraft:", "").replace("universal_minecraft:", "")
    if block_name in ["air", "cave_air", "structure_void", "barrier", "light_block", "light"] or "glass" in block_name:
        return 0
    if "grass_block" in block_name or block_name == "grass" or "slime" in block_name:
        return 1
    if "sand" in block_name and "sandstone" not in block_name:
        return 2
    if "wool" in block_name or "cobweb" in block_name:
        return 3
    if "lava" in block_name or "fire" in block_name or "redstone_block" in block_name:
        return 4
    if block_name in ["ice", "packed_ice", "blue_ice"]:
        return 5
    if "iron_block" in block_name:
        return 6
    if "leaves" in block_name or "plant" in block_name or "vine" in block_name or "fern" in block_name or "tallgrass" in block_name or "sapling" in block_name or "sugar_cane" in block_name:
        return 7
    if "snow" in block_name or "powder_snow" in block_name:
        return 8
    if "clay" in block_name:
        return 9
    if "dirt" in block_name or "podzol" in block_name or "farmland" in block_name or "coarse_dirt" in block_name or "path" in block_name:
        return 10
    if "water" in block_name or "kelp" in block_name or "seagrass" in block_name:
        return 12
    if "wood" in block_name or "log" in block_name or "planks" in block_name:
        return 13
    if "quartz" in block_name or "diorite" in block_name:
        return 14
    if "orange" in block_name or "acacia" in block_name:
        return 15
    if "stone" in block_name or "cobblestone" in block_name or "andesite" in block_name or "gravel" in block_name or "bedrock" in block_name or "ore" in block_name or "granite" in block_name:
        return 11
    return 11 # Default

def main():
    print("Loading setting and color data...")
    with open("Setting.json", "r", encoding="utf-8") as f:
        settings = json.load(f)
        
    with open("../mapData/MapColor.json", "r", encoding="utf-8") as f:
        map_color_data = json.load(f)
        
    color_dict = {}
    for item in map_color_data:
        color_dict[item["id"]] = tuple(item["rgb"])

    os.makedirs("../mapData/JSON", exist_ok=True)
    os.makedirs("../mapData/image", exist_ok=True)

    print("Loading level...")
    level = amulet.load_level("./WorldData")
    
    areas = set()
    for box in settings.get("load_area", []):
        min_ax = math.floor(box["x_min"] / 128)
        max_ax = math.floor(box["x_max"] / 128)
        min_az = math.floor(box["z_min"] / 128)
        max_az = math.floor(box["z_max"] / 128)
        for ax in range(min_ax, max_ax + 1):
            for az in range(min_az, max_az + 1):
                areas.add((ax, az))
                
    min_y = level.bounds("minecraft:overworld").min[1]
    max_y = level.bounds("minecraft:overworld").max[1]
    print(f"World bounds: Y from {min_y} to {max_y}")

    for area_X, area_Z in areas:
        print(f"Generating area {area_X}_{area_Z}...")
        colors = np.zeros((128, 128), dtype=int)
        y_coords = np.full((128, 128), min_y - 1, dtype=int)

        for cx_offset in range(8):
            for cz_offset in range(8):
                cx = area_X * 8 + cx_offset
                cz = area_Z * 8 + cz_offset
                try:
                    chunk = level.get_chunk(cx, cz, "minecraft:overworld")
                except Exception:
                    continue
                
                if chunk is None:
                    continue
                
                palette_map = {}
                for i, block in enumerate(chunk.block_palette):
                    palette_map[i] = get_map_color(block.base_name)
                
                try:
                    blocks = np.array(chunk.blocks[0:16, min_y:max_y, 0:16])
                except Exception as e:
                    print(f"Error reading block data for chunk {cx},{cz}: {e}")
                    continue
                
                # Transform blocks to colors using palette
                # Ensure otypes=[np.intc] to handle numpy mapping gracefully
                color_blocks = np.vectorize(lambda x: palette_map.get(x, 0), otypes=[np.intc])(blocks)
                
                mask = color_blocks != 0
                mask_rev = mask[:, ::-1, :]
                highest_y_rev = np.argmax(mask_rev, axis=1)
                has_non_zero = np.any(mask_rev, axis=1)
                highest_y = blocks.shape[1] - 1 - highest_y_rev
                
                for x_rel in range(16):
                    for z_rel in range(16):
                        if has_non_zero[x_rel, z_rel]:
                            y_idx = highest_y[x_rel, z_rel]
                            col = color_blocks[x_rel, y_idx, z_rel]
                            abs_y = min_y + y_idx
                            x_global = cx_offset * 16 + x_rel
                            z_global = cz_offset * 16 + z_rel
                            colors[x_global, z_global] = col
                            y_coords[x_global, z_global] = abs_y

        data = {
            "colors": colors.tolist(),
            "y_coords": y_coords.tolist()
        }
        with open(f"../mapData/JSON/{area_X}_{area_Z}.json", "w", encoding="utf-8") as f:
            json.dump(data, f)
            
        img = Image.new("RGBA", (128, 128), (0,0,0,0))
        pixels = img.load()
        for x in range(128):
            for z in range(128):
                c = colors[x, z]
                if c != 0:
                    rgb = color_dict.get(c, (0,0,0))
                    pixels[x, z] = (rgb[0], rgb[1], rgb[2], 255)
        img.save(f"../mapData/image/{area_X}_{area_Z}.png")

    level.close()
    print("Generation complete!")

if __name__ == '__main__':
    main()
