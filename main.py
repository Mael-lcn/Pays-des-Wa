import os
import sys

import bpy

chemin_dossier = "/Users/maellecene/Desktop/COURS_S2/IG3D/TMEs/tme4/src"

# 2. On dit à Python d'ajouter ce dossier à sa liste de recherche
if chemin_dossier not in sys.path:
    sys.path.append(chemin_dossier)


from utils import bprint
import island



# =============================================================================
# --- ZONE DE TEST POUR BLENDER ---
# =============================================================================
if __name__ == "__main__":
    # Nettoie toute la scène 3D pour repartir de zéro à chaque exécution du script
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


    # On définit d'abord la base (l'île principale)
    # Elle servira de point de référence pour le Z
    wano_base_config = {
        "name": "Wano_Base",
        "radius": 150.0,
        "rim_height": 30.0,
        "rim_thickness": 18.0,
        "spike_depth": 155.0,
        "rock_protrusion": 20.0,
        "rock_width": 20.0,
        "stretch_z": 1.5,
        "micro_detail": 0.5,
        "location": (0, 0, 50) # Z de référence = 50
    }

    offset_z = 10


    wano_islands_data = [
        wano_base_config,
        {
            "name": "Capitale_des_Fleurs",
            "radius": 30.0,
            "rim_height": 2.0,
            "rim_thickness": 5.0,
            "spike_depth": 10.0,
            "rock_protrusion": 1.5,
            "rock_width": 20.0,
            "stretch_z": 0.8,
            "micro_detail": 0.1,
            # On récupère X et Y de la base, et on ajoute l'offset au Z
            "location": (wano_base_config["location"][0], 
                         wano_base_config["location"][1], 
                         wano_base_config["location"][2] + offset_z)
        },
        {
            "name": "Onigashima",
            "radius": 20.0,
            "rim_height": 7.0,
            "rim_thickness": 1.0,
            "spike_depth": 10.0,
            "rock_protrusion": 6.0,
            "rock_width": 5.0,
            "stretch_z": 3.0,
            "micro_detail": 0.5,
            # Onigashima est décalée en Y (-100) et plus haute (Z + 20)
            "location": (wano_base_config["location"][0], 
                         wano_base_config["location"][1] - 100, 
                         wano_base_config["location"][2] + offset_z + 30)
        },
        {
            "name": "Kuri",
            "radius": 35.0,
            "rim_height": 8.0,
            "rim_thickness": 8.0,
            "spike_depth": 20.0,
            "rock_protrusion": 5.0,
            "rock_width": 15.0,
            "stretch_z": 1.1,
            "location": (wano_base_config["location"][0] - 70, 
                         wano_base_config["location"][1] - 50, 
                         wano_base_config["location"][2] + offset_z)
        },
        {
            "name": "Udon",
            "radius": 40.0,
            "rim_height": 12.0,
            "rim_thickness": 10.0,
            "spike_depth": 25.0,
            "rock_protrusion": 8.0,
            "rock_width": 10.0,
            "stretch_z": 0.7,
            "location": (wano_base_config["location"][0] + 70, 
                         wano_base_config["location"][1] - 40, 
                         wano_base_config["location"][2] + offset_z)
        },
        {
            "name": "Ringo",
            "radius": 35.0,
            "rim_height": 5.0,
            "rim_thickness": 5.0,
            "spike_depth": 15.0,
            "rock_protrusion": 4.0,
            "stretch_z": 1.8,
            "location": (wano_base_config["location"][0] + 30, 
                         wano_base_config["location"][1] + 70, 
                         wano_base_config["location"][2] + offset_z)
        },
        {
            "name": "Hakumai",
            "radius": 35.0,
            "rim_height": 3.0,
            "rim_thickness": 6.0,
            "spike_depth": 10.0,
            "stretch_z": 0.9,
            "location": (wano_base_config["location"][0] + 80, 
                         wano_base_config["location"][1] + 20, 
                         wano_base_config["location"][2] + offset_z)
        },
        {
            "name": "Kibi",
            "radius": 38.0,
            "rim_height": 2.0,
            "rim_thickness": 4.0,
            "spike_depth": 12.0,
            "stretch_z": 0.6,
            "location": (wano_base_config["location"][0] - 80, 
                         wano_base_config["location"][1] + 20, 
                         wano_base_config["location"][2] + offset_z)
        }
    ]

    
    # --- Boucle de génération ---
    toutes_les_iles = []

    for wano_island in wano_islands_data:
        bprint(f"Création de la région : {wano_island['name']}...")

        toutes_les_iles.append(island.create_massive_vertical_fortress(**wano_island))


    bprint("--- L'archipel de Wano est complètement généré ! ---")


