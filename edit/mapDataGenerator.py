import amulet
import os
import json
import math
import numpy as np
from PIL import Image

def get_map_color(base_name, full_name):
    base_name = base_name.lower().replace("minecraft:", "").replace("universal_minecraft:", "")
    full_name = full_name.lower()
    
    if base_name in ["air", "cave_air", "structure_void", "barrier", "light_block", "light"] or "glass" in base_name or "torch" in base_name:
        return 0
        
    if "terracotta" in full_name or "hardened_clay" in full_name:
        if "white" in full_name: return 36
        if "orange" in full_name: return 37
        if "magenta" in full_name: return 38
        if "light_blue" in full_name: return 39
        if "yellow" in full_name: return 40
        if "lime" in full_name: return 41
        if "pink" in full_name: return 42
        if "light_gray" in full_name or "silver" in full_name: return 44
        if "gray" in full_name: return 43
        if "cyan" in full_name: return 45
        if "purple" in full_name: return 46
        if "blue" in full_name: return 47
        if "brown" in full_name: return 48
        if "green" in full_name: return 49
        if "red" in full_name: return 50
        if "black" in full_name: return 51
        return 35 # Default Terracotta
        
    if "concrete" in full_name or "wool" in full_name or "carpet" in full_name:
        if "white" in full_name: return 8
        if "orange" in full_name: return 15
        if "magenta" in full_name: return 16
        if "light_blue" in full_name: return 17
        if "yellow" in full_name: return 18
        if "lime" in full_name: return 19
        if "pink" in full_name: return 20
        if "light_gray" in full_name or "silver" in full_name: return 22
        if "gray" in full_name: return 21
        if "cyan" in full_name: return 23
        if "purple" in full_name: return 24
        if "blue" in full_name: return 25
        if "brown" in full_name: return 26
        if "green" in full_name: return 27
        if "red" in full_name: return 28
        if "black" in full_name: return 29
        return 8
        
    if "granite" in base_name: return 36 # Pinkish white terracotta suits granite
    if "diorite" in base_name: return 22 # Light gray
    if "andesite" in base_name: return 6 # Iron color (brighter than stone)
    if "quartz" in base_name: return 14

    if "grass_block" in base_name or base_name == "grass" or "slime" in base_name:
        return 1
    if "sand" in base_name and "sandstone" not in base_name:
        return 2
    if "cobweb" in base_name:
        return 3
    if "lava" in base_name or "fire" in base_name or "redstone_block" in base_name:
        return 4
    if base_name in ["ice", "packed_ice", "blue_ice"]:
        return 5
    if "iron_block" in base_name:
        return 6
    if "leaves" in base_name or "plant" in base_name or "vine" in base_name or "fern" in base_name or "tallgrass" in base_name or "sapling" in base_name or "sugar_cane" in base_name:
        return 7
    if "snow" in base_name or "powder_snow" in base_name:
        return 8
    if "clay" in base_name:
        return 9
    if "dirt" in base_name or "podzol" in base_name or "farmland" in base_name or "coarse_dirt" in base_name or "path" in base_name:
        return 10
    if "water" in base_name or "kelp" in base_name or "seagrass" in base_name:
        return 12
    if "wood" in base_name or "log" in base_name or "planks" in base_name:
        return 13
    if "stone" in base_name or "cobblestone" in base_name or "gravel" in base_name or "bedrock" in base_name or "ore" in base_name:
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
                    props_str = ""
                    try:
                        props_str = ",".join(f"{k}={v}" for k, v in block.properties.items())
                    except Exception:
                        pass
                    block_full_str = f"{block.base_name}[{props_str}]"
                    palette_map[i] = get_map_color(block.base_name, block_full_str)
                
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
                    
                    # 影の計算 (北側 z-1 との高さの差分で陰影をつける)
                    factor = 1.0
                    if z > 0:
                        y_diff = y_coords[x, z] - y_coords[x, z-1]
                        if y_diff > 0:
                            factor = 1.2  # 北より高い場合は明るくする
                        elif y_diff < 0:
                            factor = 0.8  # 北より低い場合は暗くする
                    
                    r = min(255, int(rgb[0] * factor))
                    g = min(255, int(rgb[1] * factor))
                    b = min(255, int(rgb[2] * factor))
                    
                    pixels[x, z] = (r, g, b, 255)
        img.save(f"../mapData/image/{area_X}_{area_Z}.png")

    level.close()
    print("Generation complete!")

if __name__ == '__main__':
    main()
