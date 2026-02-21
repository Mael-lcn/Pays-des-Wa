import numpy as np
import math

import bpy



def create_massive_vertical_fortress(
    name="Onigashima_Base", 
    radius=50.0, 
    rim_height=20.0, 
    rim_thickness=15.0, 
    spike_depth=40.0, 
    rock_protrusion=6.0, 
    rock_width=10.0, 
    stretch_z=3.5,
    micro_detail=0.5,
    location=(0, 0, 0)
):
    """
    Génère la base rocheuse d'Onigashima (ou une îles de Wano) avec de larges piliers rocheux verticaux.
    L'île possède un plateau intérieur plat, entouré d'une haute falaise, et se termine en pic asymétrique en dessous.

    Args:
        name (str): Le nom de l'objet généré dans la scène Blender.
        radius (float): Le rayon total de l'île (incluant la falaise extérieure).
        rim_height (float): La hauteur maximale des falaises qui encerclent le plateau.
        rim_thickness (float): L'épaisseur de ces falaises extérieures.
        spike_depth (float): La profondeur du pic rocheux sous l'île.
        rock_protrusion (float): La force avec laquelle les gros rochers ressortent de la paroi.
        rock_width (float): La largeur/épaisseur des blocs rocheux verticaux (échelle du bruit Voronoi).
        stretch_z (float): Le facteur d'étirement vertical de l'île (crée l'effet de colonnes de basalte).
        micro_detail (float): L'intensité des petites aspérités de surface sur les gros blocs.
        location (tuple): Les coordonnées (X, Y, Z) où placer le centre du plateau de l'île.

    Returns:
        bpy.types.Object: L'objet Blender généré.
    """
    # =========================================================================
    # 1. CRÉATION DE LA GÉOMÉTRIE DE BASE
    # =========================================================================

    # Ajoute une sphère UV qui servira de "pâte à modeler" de base
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=128,  # Nombre de découpes verticales (haute résolution requise pour les détails)
        ring_count=64, # Nombre de découpes horizontales
        radius=radius, # Applique le rayon total demandé
        location=location # Place l'objet aux coordonnées demandées
    )

    # Récupère l'objet fraîchement créé pour le manipuler
    island = bpy.context.active_object

    # Renomme l'objet pour garder la scène propre
    island.name = name

    # =========================================================================
    # 2. PRÉPARATION DU MASQUE (POUR PROTÉGER LE PLATEAU PLAT)
    # =========================================================================

    # Crée un groupe de sommets (Vertex Group) qui agira comme un masque de peinture
    vg = island.vertex_groups.new(name="Rock_Mask")

    # Calcule à partir de quel rayon (en partant du centre) la falaise doit commencer à monter
    plateau_radius = radius - rim_thickness

    # =========================================================================
    # 3. SCULPTURE MATHÉMATIQUE DE LA FORME (BOL + PIC)
    # =========================================================================

    # Parcourt chaque sommet (point 3D) de la sphère pour modifier sa position
    for v in island.data.vertices:

        # Calcule la distance 'r' du point par rapport au centre sur le plan 2D (axes X et Y)
        r = math.hypot(v.co.x, v.co.y)

        # Si le point est sur la moitié haute de la sphère d'origine (Z positif)
        if v.co.z >= 0:

            # Si le point est à l'intérieur de la zone du plateau
            if r < plateau_radius:
                # On écrase sa hauteur à 0 pour créer un sol parfaitement plat
                v.co.z = 0
                # On lui assigne un poids de 0 dans le masque : les rochers ne l'affecteront pas
                vg.add([v.index], 0.0, 'REPLACE')

            # Si le point est sur les bords extérieurs (la future muraille)
            else:
                # On calcule une progression de 0 à 1 depuis le bord du plateau jusqu'au bord de l'île
                normalized_r = (r - plateau_radius) / rim_thickness

                # On calcule la hauteur cible (plus on s'éloigne, plus ça monte vers rim_height)
                z_target = normalized_r * rim_height

                # On applique la hauteur tout en divisant par stretch_z (pour compenser l'étirement final)
                v.co.z = z_target / stretch_z 

                # On assigne un poids de 1 : cette zone sera complètement déformée par la roche
                vg.add([v.index], 1.0, 'REPLACE')
   
        # Si le point est sur la moitié basse de la sphère d'origine (Z négatif, le fond de l'île)
        else:
            # On calcule à quel point on est bas sur la sphère d'origine (de 0 à 1)
            normalized_z = (v.co.z + radius) / radius

            # On calcule la profondeur cible (ça descend de la base de la falaise jusqu'au pic)
            z_target = -spike_depth + normalized_z * (rim_height + spike_depth)

            # On applique la position Z avec la même compensation d'étirement
            v.co.z = z_target / stretch_z 

            # Poids 1 : le dessous de l'île sera 100% rocheux
            vg.add([v.index], 1.0, 'REPLACE')

    # Force Blender à actualiser le maillage pour prendre en compte nos modifications mathématiques
    island.data.update()

    # =========================================================================
    # ÉTIREMENT VERTICAL (SCALE Z)
    # =========================================================================
    # On multiplie l'échelle Z de l'objet. Comme le bruit 3D sera évalué après, 
    # cela va étirer les "bulles" de bruit en de grandes colonnes rocheuses !
    island.scale[2] = stretch_z

    # =========================================================================
    # 4. SUBDIVISION (LISSAGE ET DÉTAIL)
    # =========================================================================

    # Ajoute un modificateur Subdivision Surface pour avoir assez de polygones à déformer
    subsurf = island.modifiers.new(name="Subdiv", type='SUBSURF')
    subsurf.levels = 2 # Niveau de détail dans la vue 3D
    subsurf.render_levels = 3 # Niveau de détail au moment du calcul de l'image (Rendu final)

    # =========================================================================
    # 5. MACRO-RELIEF : LES LARGES PILIERS ROCHEUX (VORONOI)
    # =========================================================================

    # Crée une texture procédurale Voronoi (pour la roche taillée)
    tex_macro = bpy.data.textures.new("Macro_Rock_Thick", type='VORONOI')
    tex_macro.distance_metric = 'DISTANCE' # Utilise le mode 'Distance' pour avoir des pics/cratères

    # Règle la taille du motif : une grande valeur fait de très larges blocs de pierre
    tex_macro.noise_scale = rock_width 

    # Ajoute le modificateur "Displace" pour déformer physiquement la surface
    mod_macro = island.modifiers.new(name="Macro_Deform", type='DISPLACE')
    mod_macro.texture = tex_macro # Lie la texture Voronoi

    # La force définit de combien de mètres les rochers vont jaillir hors de la paroi
    mod_macro.strength = rock_protrusion 

    # Applique le masque pour protéger notre plateau plat des déformations !
    mod_macro.vertex_group = "Rock_Mask"

    # =========================================================================
    # 6. MICRO-RELIEF : ASPÉRITÉS DE SURFACE
    # =========================================================================

    # Crée une texture de type "Nuages" pour ajouter du grain à la pierre
    tex_micro = bpy.data.textures.new("Micro_Rock", type='CLOUDS')
    tex_micro.noise_scale = 1.0 # Petits détails

    # Ajoute un second modificateur Displace par-dessus les gros blocs
    mod_micro = island.modifiers.new(name="Micro_Deform", type='DISPLACE')
    mod_micro.texture = tex_micro
    mod_micro.strength = micro_detail # Force très faible pour ne pas détruire les gros piliers
    mod_micro.vertex_group = "Rock_Mask" # Protège encore le plateau

    # Ordonne à Blender de lisser les ombres des polygones (retire l'effet "facettes")
    bpy.ops.object.shade_smooth()

    # =========================================================================
    # 7. MATÉRIAU
    # =========================================================================

    mat_name = "Wano_Manga_Rock"
    # Vérifie si le matériau existe déjà dans le fichier pour ne pas le créer 50 fois
    if mat_name not in bpy.data.materials:
        # Crée le matériau
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True # Active l'éditeur nodal
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
    
        # Supprime les noeuds par défaut (sauf la sortie) pour faire table rase
        for node in nodes:
            if node.type != 'OUTPUT_MATERIAL':
                nodes.remove(node)

        # Récupère le noeud de sortie (Material Output)
        output_node = nodes.get("Material Output")
        
        # Crée le shader principal (Principled BSDF)
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        bsdf.inputs["Roughness"].default_value = 0.9 # Pierre très mate (pas de brillance)
    
        # Crée un nœud de Bruit (Noise Texture) pour mélanger les couleurs aléatoirement
        noise = nodes.new(type='ShaderNodeTexNoise')
        noise.location = (-600, 0)
        noise.inputs["Scale"].default_value = 5.0 # Taille des taches de couleur

        # Crée un dégradé (ColorRamp) pour choisir les couleurs exactes
        ramp = nodes.new(type='ShaderNodeValToRGB')
        ramp.location = (-300, 0)

        # Ajoute la première couleur : Un Saumon / Ocre
        ramp.color_ramp.elements[0].position = 0.3
        ramp.color_ramp.elements[0].color = (0.85, 0.55, 0.40, 1.0) 

        # Ajoute la deuxième couleur : Un Beige clair
        ramp.color_ramp.elements[1].position = 0.7
        ramp.color_ramp.elements[1].color = (0.95, 0.85, 0.65, 1.0) 

        # Connecte la sortie du bruit à l'entrée du dégradé
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])

        # Connecte les couleurs générées au Shader
        links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

        # Connecte le Shader à la surface de l'objet final
        links.new(bsdf.outputs["BSDF"], output_node.inputs["Surface"])
    else:
        # Si le matériau existait déjà, on le récupère simplement
        mat = bpy.data.materials[mat_name]

    # Applique le matériau à l'île
    island.data.materials.append(mat)

    # Retourne l'objet 3D prêt à l'emploi ^^
    return island





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

    for island in wano_islands_data:
        print(f"Création de la région : {island['name']}...")

        nouvelle_ile = create_massive_vertical_fortress(**island)

        toutes_les_iles.append(nouvelle_ile)


    print("--- L'archipel de Wano est complètement généré ! ---")




