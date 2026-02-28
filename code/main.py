import os
import sys
import importlib
import bpy



# On essaie d'abord de trouver où est le fichier .blend (s'il a été sauvegardé)
dossier_racine = os.path.dirname(bpy.data.filepath)

#  Si le .blend est totalement vierge/non sauvegardé
if not dossier_racine:
    #On regarde si Blender sait d'où vient le texte "main.py" 
    if "main.py" in bpy.data.texts and bpy.data.texts["main.py"].filepath:
        chemin_du_script = bpy.data.texts["main.py"].filepath
        # Le script est dans /code/main.py, on remonte d'un dossier pour trouver la racine
        dossier_racine = os.path.dirname(os.path.dirname(chemin_du_script))
    else:
        print("Erreur dossier introuvable")
        

# On pointe vers le dossier "code"
chemin_dossier = os.path.join(dossier_racine, "code")

# On ajoute le dossier au système pour que les imports fonctionnent
if chemin_dossier not in sys.path:
    sys.path.append(chemin_dossier)

from utils import bprint
#importlib.reload(utils)

import island
importlib.reload(island)


import udon
importlib.reload(udon)

import city
importlib.reload(city)

import Onigashima 
importlib.reload(Onigashima)
import Ringo 
importlib.reload(Ringo)

import water
importlib.reload(water)






# =============================================================================
# --- ZONE DE TEST POUR BLENDER ---
# =============================================================================
if __name__ == "__main__":
    objets_proteges = ["maison_pauvre", "maison_riche", "arbre", "maison_shogun", "pont", "grand_arbre", "temple","tori","Plane_sakura","Wind_sakura","turbulence_sakura","Sakura"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type not in ['CAMERA', 'LIGHT']:
            # On vérifie si le nom de l'objet fait partie de tes assets
            nom_base = obj.name.split('.')[0] # Permet d'ignorer les .001 si tu as fait des copies
            if nom_base not in objets_proteges and obj.name in bpy.context.view_layer.objects:
                    obj.select_set(True) # Sélectionne pour suppression uniquement ce qui n'est pas protégé
                
    bpy.ops.object.delete()

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
            "rim_height": 5.0,
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
    toutes_les_iles = {}

    for wano_island in wano_islands_data:

        bprint(f"Création de la région : {wano_island['name']}...")

        toutes_les_iles[wano_island['name']] = island.create_massive_vertical_fortress(**wano_island)


    Onigashima.construire(toutes_les_iles["Onigashima"])
    Ringo.construire(toutes_les_iles["Ringo"])


    # ... (Création de l'eau) ...
    bprint("Création de l'Océan intérieur...")
    hauteur_eau = wano_base_config["location"][2] + 5.0

    # 1. On réduit un peu plus le rayon de l'eau (-12.0) pour qu'elle ne fuite plus par les falaises
    rayon_eau = wano_base_config["radius"] - 12.0 
    water.create_water(
        name="Eau_Wano", 
        radius=rayon_eau, 
        location=(0, 0, hauteur_eau)
    )

    bprint("Création de la Grande Cascade...")
    hauteur_cascade = 160.0
    y_bord_ile = wano_base_config["location"][1] - wano_base_config["radius"] + 2
    
    water.create_waterfall(
        name="Grande_Cascade",
        width=42.0,
        height=hauteur_cascade,
        location=(0, y_bord_ile, hauteur_eau) 
    )

    bprint("Percement de la muraille pour la cascade...")

    bpy.ops.mesh.primitive_cube_add(
        size=1.0, 
        location=(0, y_bord_ile, 0.0) 
    )
    cutter = bpy.context.active_object
    cutter.name = "Decoupe_Cascade"

    # Et on le rend GIGANTESQUE en hauteur (200m de Z) pour qu'il tranche la roche jusqu'en bas !
    cutter.scale = (38.0, 25, 200.0)

    cutter.hide_viewport = True
    cutter.hide_render = True
    cutter.display_type = 'WIRE'

    wano_base = bpy.data.objects.get("Wano_Base")
    if wano_base:
        bool_mod = wano_base.modifiers.new(name="Trou_Cascade", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = cutter
        
        bpy.context.view_layer.objects.active = wano_base
        bpy.ops.object.modifier_move_to_index(modifier="Trou_Cascade", index=0)
        
        
        
        bprint("Construction de la Capitale des Fleurs...")
    
    config_capitale = wano_islands_data[1] 
    loc_capitale = config_capitale["location"]
    rayon_plateau_capitale = config_capitale["radius"] - config_capitale["rim_thickness"]
    
    city.generer_capitale(
        nom_ile=config_capitale["name"], 
        centre_ile=loc_capitale, 
        rayon_plateau=rayon_plateau_capitale, 
        nb_maisons=110, 
       nb_arbres=140
    )
    

# ==========================================
    # GÉNÉRATION D'UDON
    # ==========================================
    bprint("Construction de la prison d'Udon...")
    
    config_udon = wano_islands_data[3] 
    loc_udon = config_udon["location"]
    rayon_plateau_udon = config_udon["radius"] - config_udon["rim_thickness"]
    
    udon.generer_udon(
        nom_ile=config_udon["name"],
        centre_ile=loc_udon, 
        rayon_plateau=rayon_plateau_udon
    )

    bprint("--- L'archipel de Wano est complètement généré ! ---")

