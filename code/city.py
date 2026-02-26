import bpy
import random
import math
from mathutils import Vector
import time
from utils import bprint
random.seed(time.time())

# ==========================================
# 🎨 1. NOS PALETTES DE COULEURS
# ==========================================

PALETTE_SAMOURAI = [
    (0.12, 0.15, 0.35, 1.0), 
    (0.25, 0.10, 0.35, 1.0), 
    (0.15, 0.30, 0.18, 1.0), 
    (0.40, 0.10, 0.12, 1.0), 
    (0.10, 0.10, 0.10, 1.0)  
]

PALETTE_ARBRES = [
    #(0.05, 0.25, 0.05, 1.0), # vert
    #(0.1, 0.4, 0.1, 1.0),    # vert clair
    (0.8, 0.2, 0.4, 1.0),    
    (0.906, 0.412, 0.804, 1.0),  
    #(0.3, 0.1, 0.4, 1.0),   
    (0.784, 0.235, 0.690, 1.0), 
   (0.878, 0.749, 0.988, 1.0)
]

# ==========================================
#  LES OUTILS DE BASE
# ==========================================







def placer_objet_fixe(nom_objet,position, collection=None,rotation=(0.0, 0.0, 0.0), echelle=(1.0, 1.0, 1.0)):
    obj_source = bpy.data.objects.get(nom_objet)
    if not obj_source:

        bprint(f"⚠️ ERREUR FATALE : Objet introuvable : '{nom_objet}'. Vérifie son nom exact dans Blender !")
        return None
        
    nouvel_obj = obj_source.copy()
    if nouvel_obj.data: 
        nouvel_obj.data = obj_source.data
    if collection :     
        collection.objects.link(nouvel_obj)
    nouvel_obj.location = Vector(position)
    nouvel_obj.rotation_euler = rotation
    nouvel_obj.scale = echelle
    return nouvel_obj




def modifier_apparence_materiau(objet, nom_partie_a_cibler, couleur_base, rugosite=0.8, metallique=0.0):
    if not objet.material_slots: return 
    for slot in objet.material_slots:
        if slot.material and nom_partie_a_cibler.lower() in slot.material.name.lower():
            mat_unique = slot.material.copy()
            slot.link = 'OBJECT' 
            slot.material = mat_unique
            if mat_unique.use_nodes and mat_unique.node_tree:
                noeuds = mat_unique.node_tree.nodes
                if "Principled BSDF" in noeuds:
                    bsdf = noeuds["Principled BSDF"]
                    bsdf.inputs["Base Color"].default_value = couleur_base
                    bsdf.inputs["Roughness"].default_value = rugosite
                    bsdf.inputs["Metallic"].default_value = metallique
                    
            

def transformer_objet(objet, cible_x, cible_y, echelle_min, echelle_max, est_maison):
    taille = random.uniform(echelle_min, echelle_max)
    objet.scale = (taille, taille, taille)
    if est_maison:
        angle = math.atan2(cible_y - objet.location.y, cible_x - objet.location.x)
        objet.rotation_euler[2] = angle + (math.pi / 2)
    else:
        objet.rotation_euler[2] = random.uniform(0, 2 * math.pi)


def trouver_point_sur_terrain(nom_terrain, positions_deja_prises, distance_min):
    obj_terrain = bpy.data.objects.get(nom_terrain)
    if not obj_terrain: return None
    
    # On calcule le rayon réel du tapis (en prenant la plus grande dimension)
    rayon_max = max(obj_terrain.dimensions.x, obj_terrain.dimensions.y) / 2.0
    
    #on fait jusqu'à 30 tentatives pour trouver un point vert valide
    for _ in range(30):
        # 1. Génération d'un point aléatoire uniformément réparti dans un cercle
        angle = random.uniform(0, 2 * math.pi)
        # math.sqrt permet de bien répartir les maisons partout, et pas juste au centre !
        r = rayon_max * math.sqrt(random.random()) 
        
        rel_x = r * math.cos(angle)
        rel_y = r * math.sin(angle)
        

        loc_abs = Vector((
            obj_terrain.location.x + rel_x,
            obj_terrain.location.y + rel_y,
            obj_terrain.location.z
        ))
        

        dist_centre = math.hypot(rel_x, rel_y)
        dist_nw = math.hypot(rel_x - (-16.0), rel_y - 15.0)
        
        est_valide = True
        
        # On évite que ça déborde dans le vide au bord de l'île (marge de 2m)
        if dist_centre > rayon_max - 2.0: est_valide = False
            
        # On évite la Montagne Shogun et ses douves (eau jusqu'à 11.5m)
        if dist_centre < 11.5: est_valide = False
            
        #on évite la Montagne Neige (Rayon de 5m)
        if dist_nw < 5: est_valide = False
            
        # on évite la Rivière Nord
        if rel_y > 0.0 and abs(rel_x) < 4.5 and dist_centre >= 11.0: est_valide = False
            
        # on évite L'Allée Centrale Sud (Largeur 1.5m de sécurité de chaque côté)
        if abs(rel_x) < 1.5 and rel_y < -10.5: est_valide = False
            
        if not est_valide:
            continue # Point invalide, on annule et on boucle pour en chercher un autre !
            
        # on vérifie qu'on ne chevauche pas une autre maison ou arbre
        collision = False
        if positions_deja_prises is not None:
            for pos_prise in positions_deja_prises:
                rayon_obstacle = pos_prise.get("radius", distance_min) 
                if (loc_abs - pos_prise["loc"]).length < rayon_obstacle: 
                    collision = True
                    break
                    
        if not collision:
            return loc_abs # ✅ Point parfait trouvé sur l'herbe !
            
    return None # Échec après 30 tentatives

# ==========================================
 #LES MÉTHODES DE GÉNÉRATION (Unitaires)
# ==========================================

def generer_maison(type_maison, nom_terrain, collection, positions_placees=None, position_exacte=None):
    obj_source = bpy.data.objects.get(type_maison)
    if not obj_source: return False

    impact = position_exacte
    if impact is None:

        impact = trouver_point_sur_terrain(nom_terrain, positions_placees, 2.5)
        
    if impact:
        nouvel_obj = obj_source.copy()
        if nouvel_obj.data: nouvel_obj.data = obj_source.data
        collection.objects.link(nouvel_obj)
        nouvel_obj.location = impact
        
        transformer_objet(nouvel_obj, 0.0, 5.0, 0.9, 1.1, est_maison=True)
        coul = random.choice(PALETTE_SAMOURAI)
        modifier_apparence_materiau(nouvel_obj, "toit", coul, rugosite=0.9)
        
        if positions_placees is not None and position_exacte is None:
            positions_placees.append({"loc": impact})
        return True
    return False

def generer_arbre(nom_arbre, nom_terrain, collection, positions_placees=None, position_exacte=None):
    obj_source = bpy.data.objects.get(nom_arbre)
    if not obj_source: return False

    impact = position_exacte
    if impact is None:

        impact = trouver_point_sur_terrain(nom_terrain, positions_placees, 1)
        
    if impact:
        nouvel_obj = obj_source.copy()
        if nouvel_obj.data: nouvel_obj.data = obj_source.data
        collection.objects.link(nouvel_obj)
        nouvel_obj.location = impact
        
        transformer_objet(nouvel_obj, 0.0, 5.0, 0.6, 1.4, est_maison=False)
        
        coul = random.choice(PALETTE_ARBRES)
        est_rose = coul[0] > 0.7 and coul[1] < 0.6 
        metal =  0.0
        rugosite = 0.3 if est_rose else 0.8
        modifier_apparence_materiau(nouvel_obj, "feuill", coul, rugosite=rugosite, metallique=metal)
        
        if positions_placees is not None and position_exacte is None:
            positions_placees.append({"loc": impact})
        return True
    return False

# ==========================================
# 🏘️ 4. LES MÉTHODES DE GROUPES (Plurielles)
# ==========================================

def generer_maisons(nb_cible, types_maisons_possibles, nom_terrain, collection, positions_placees):
    posees = 0
    tentatives = 0
    while posees < nb_cible and tentatives < (nb_cible * 50):
        tentatives += 1
        type_choisi = random.choice(types_maisons_possibles)
        if generer_maison(type_choisi, nom_terrain, collection, positions_placees):
            posees += 1
    return posees

def generer_arbres(nb_cible, nom_arbre, nom_terrain, collection, positions_placees):
    poses = 0
    tentatives = 0
    while poses < nb_cible and tentatives < (nb_cible * 50):
        tentatives += 1
        if generer_arbre(nom_arbre, nom_terrain, collection, positions_placees):
            poses += 1
    return poses



    # ==========================================
# ⛰️  SCULPTURE SUR-MESURE DE L'ÎLE
# ==========================================
def sculpter_ile_capitale(nom_ile):
    """ Prend l'île générée et soulève le terrain pour faire les montagnes avec des sommets plats """
    ile = bpy.data.objects.get(nom_ile)
    if not ile: return

    scale_z = ile.scale[2]
    
    for v in ile.data.vertices:
        if abs(v.co.z) < 0.001:
            x, y = v.co.x, v.co.y
            z_val = 0.0
            
            # 1. Montagne Centrale Shogun
            dist_centre = math.hypot(x, y)
            if dist_centre < 7.0:
                hauteur_courbe = math.cos(dist_centre / 7.0 * (math.pi / 2)) * 15.0
                z_val = max(z_val, min(hauteur_courbe, 12.0))
                
            # 2. L'EAU AUTOUR DE LA MONTAGNE (Les Douves)
            elif dist_centre >= 7.0 and dist_centre < 11.0:
                z_val = -2.0
                
            # 3. Grande Montagne Neige (DÉCALÉE À GAUCHE 🎯 : x - (-16.0))
            dist_nw = math.hypot(x - (-16.0), y - 15.0)
            if dist_nw < 4.5:
                hauteur_courbe = math.cos(dist_nw / 4.5 * (math.pi / 2)) * 30.0
                z_val = max(z_val, min(hauteur_courbe, 27.0))
                
            # 4. LA RIVIÈRE DERRIÈRE
            if y > 0.0 and abs(x) < 4.0 and dist_centre >= 11.0 and dist_nw > 4.5:
                z_val = -2.0 
                
            if z_val != 0.0:
                v.co.z = z_val / scale_z
                
    ile.data.update()
    
def appliquer_materiel_capitale(nom_ile):
    """ Peint l'île avec des masques vectoriels pour cibler chaque montagne et l'allée ! """
    ile = bpy.data.objects.get(nom_ile)
    if not ile: return

    def hex_to_rgba(hex_str):
        hex_str = hex_str.lstrip('#')
        r, g, b = tuple(int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        return (r**2.2, g**2.2, b**2.2, 1.0)

    mat_name = "Capitale_Smart_Material"
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear() 
    
    def new_node(ntype, x, y):
        n = nodes.new(ntype)
        n.location = (x, y)
        return n
        
    out = new_node('ShaderNodeOutputMaterial', 800, 0)
    bsdf = new_node('ShaderNodeBsdfPrincipled', 500, 0)
    bsdf.inputs["Roughness"].default_value = 0.9
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    
    coord = new_node('ShaderNodeTexCoord', -1000, 0)
    sep_obj = new_node('ShaderNodeSeparateXYZ', -800, 200)
    links.new(coord.outputs["Object"], sep_obj.inputs["Vector"])
    
    geom = new_node('ShaderNodeNewGeometry', -1000, -200)
    sep_world = new_node('ShaderNodeSeparateXYZ', -800, -200)
    links.new(geom.outputs["Position"], sep_world.inputs["Vector"])
    
    comb_xy = new_node('ShaderNodeCombineXYZ', -600, 200)
    links.new(sep_obj.outputs["X"], comb_xy.inputs["X"])
    links.new(sep_obj.outputs["Y"], comb_xy.inputs["Y"])
    
    # === MONTAGNE SHOGUN (Centre) ===
    dist_shogun = new_node('ShaderNodeVectorMath', -400, 300)
    dist_shogun.operation = 'DISTANCE'
    links.new(comb_xy.outputs[0], dist_shogun.inputs[0])
    
    mask_shogun = new_node('ShaderNodeMapRange', -200, 300)
    mask_shogun.inputs[1].default_value = 7.5 
    mask_shogun.inputs[2].default_value = 6.5  
    links.new(dist_shogun.outputs["Value"], mask_shogun.inputs["Value"])
    
    noise_shogun = new_node('ShaderNodeTexNoise', -400, 100)
    noise_shogun.inputs["Scale"].default_value = 15.0 
    links.new(coord.outputs["Object"], noise_shogun.inputs["Vector"])
    
    ramp_shogun = new_node('ShaderNodeValToRGB', -200, 100)
    ramp_shogun.color_ramp.elements[0].position = 0.55
    ramp_shogun.color_ramp.elements[0].color = hex_to_rgba('#8f7340') 
    el1 = ramp_shogun.color_ramp.elements.new(0.60)
    el1.color = hex_to_rgba('#4a614b') 
    links.new(noise_shogun.outputs["Fac"], ramp_shogun.inputs["Fac"])
    
# === MONTAGNE NORD-OUEST ===
    dist_nw = new_node('ShaderNodeVectorMath', -400, 700)
    dist_nw.operation = 'DISTANCE'
    links.new(comb_xy.outputs[0], dist_nw.inputs[0])
    # 🎯 DÉCALÉ À GAUCHE ICI AUSSI (-16.0)
    dist_nw.inputs[1].default_value = (-16.0, 15.0, 0.0)
    
    mask_nw = new_node('ShaderNodeMapRange', -200, 700)
    mask_nw.inputs[1].default_value = 5.0 
    mask_nw.inputs[2].default_value = 4.0 
    links.new(dist_nw.outputs["Value"], mask_nw.inputs["Value"])
    
    map_nw_z = new_node('ShaderNodeMapRange', -400, 500)
    map_nw_z.inputs[1].default_value = 60.0
    map_nw_z.inputs[2].default_value = 90.0
    links.new(sep_world.outputs["Z"], map_nw_z.inputs["Value"])
    
    ramp_nw = new_node('ShaderNodeValToRGB', -200, 500)
    ramp_nw.color_ramp.elements[0].position = 0.84 
    ramp_nw.color_ramp.elements[0].color = hex_to_rgba('#70a6d3') 
    el2 = ramp_nw.color_ramp.elements.new(0.86) 
    el2.color = hex_to_rgba('#bce1f7') 
    links.new(map_nw_z.outputs["Result"], ramp_nw.inputs["Fac"])
    
    # === RESTE DE L'ÎLE (Eau et Herbe) ===
    map_base = new_node('ShaderNodeMapRange', -400, -200)
    map_base.inputs[1].default_value = 58.0 
    map_base.inputs[2].default_value = 60.1 
    links.new(sep_world.outputs["Z"], map_base.inputs["Value"])
    
    ramp_base = new_node('ShaderNodeValToRGB', -200, -200)
    ramp_base.color_ramp.elements[0].position = 0.4
    ramp_base.color_ramp.elements[0].color = hex_to_rgba('#105a9c') # Bleu
    ramp_base.color_ramp.elements[1].position = 0.45
    ramp_base.color_ramp.elements[1].color = hex_to_rgba('#50873a') # Vert Herbe
    links.new(map_base.outputs["Result"], ramp_base.inputs["Fac"])
    
    # === L'ALLÉE CENTRALE === 🎯 (CORRIGÉ ICI)
    abs_x = new_node('ShaderNodeMath', -600, -400)
    abs_x.operation = 'ABSOLUTE'
    links.new(sep_obj.outputs["X"], abs_x.inputs[0])

    mask_path_x = new_node('ShaderNodeMath', -400, -400)
    mask_path_x.operation = 'LESS_THAN'
    links.new(abs_x.outputs[0], mask_path_x.inputs[0]) # 🐛 LIEN AJOUTÉ ICI
    mask_path_x.inputs[1].default_value = 1.0 

    mask_path_y = new_node('ShaderNodeMath', -400, -550)
    mask_path_y.operation = 'LESS_THAN'
    links.new(sep_obj.outputs["Y"], mask_path_y.inputs[0]) # 🐛 LIEN AJOUTÉ ICI
    mask_path_y.inputs[1].default_value = -11.0 

    mask_path = new_node('ShaderNodeMath', -200, -450)
    mask_path.operation = 'MULTIPLY'
    links.new(mask_path_x.outputs[0], mask_path.inputs[0])
    links.new(mask_path_y.outputs[0], mask_path.inputs[1])

    rgb_path = new_node('ShaderNodeRGB', -200, -600)
    rgb_path.outputs[0].default_value = hex_to_rgba('#d3bead')
    
    # === LE MÉLANGE FINAL ===
    mix_path = new_node('ShaderNodeMixRGB', 0, -200) 
    links.new(mask_path.outputs[0], mix_path.inputs["Fac"])
    links.new(ramp_base.outputs["Color"], mix_path.inputs[1]) 
    links.new(rgb_path.outputs[0], mix_path.inputs[2]) 

    mix1 = new_node('ShaderNodeMixRGB', 150, -100) 
    links.new(mask_shogun.outputs["Result"], mix1.inputs["Fac"])
    links.new(mix_path.outputs["Color"], mix1.inputs[1]) 
    links.new(ramp_shogun.outputs["Color"], mix1.inputs[2])
    
    mix2 = new_node('ShaderNodeMixRGB', 300, 0) 
    links.new(mask_nw.outputs["Result"], mix2.inputs["Fac"])
    links.new(mix1.outputs["Color"], mix2.inputs[1])
    links.new(ramp_nw.outputs["Color"], mix2.inputs[2])
    
    links.new(mix2.outputs["Color"], bsdf.inputs["Base Color"])
        
    if len(ile.data.materials) > 0:
        ile.data.materials[0] = mat
    else:
        ile.data.materials.append(mat)
# ==========================================
# ⛰️ 4.5. LA GÉNÉRATION DU DÉCOR (Hybride & Sécurisé)
# ==========================================

def creer_zone_spawn_automatique(nom_zone, rayon, location, collection):
    """ Génère un disque plat invisible si le joueur n'a pas importé de tapis """
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=rayon, depth=0.1, location=location)
    zone = bpy.context.active_object
    zone.name = nom_zone
    
    # 🎯 CORRECTION : On gère les dossiers proprement, peu importe où Blender l'a fait pop !
    # 1. On l'ajoute à notre belle collection de ville
    if zone.name not in collection.objects:
        collection.objects.link(zone)
        
    # 2. On le retire de TOUTES les autres collections (comme ça, pas d'erreur possible)
    for coll in zone.users_collection:
        if coll != collection:
            coll.objects.unlink(zone)
    
    zone.hide_viewport = True
    zone.hide_render = True
    zone.display_type = 'WIRE'
    return zone



def placer_decor_custom(collection, centre_ile, rayon_plateau, positions_memoire):
    """ Place tes éléments de level design (Montagne, Palais, Pont, Tapis, Toris) """
    bprint("🗺️ Placement du level design de la Capitale...")
    cx, cy, cz = centre_ile

    scale_factor = rayon_plateau / 10.0 

    tapis = placer_objet_fixe("Zone_Village", collection=collection, position=(cx, cy, cz + 0.1))
    
    if not tapis:
        bprint("⚠️ 'Zone_Village' non trouvé : Génération d'un tapis de spawn automatique !")
        tapis = creer_zone_spawn_automatique("Zone_Village_Auto", rayon_plateau, (cx, cy, cz + 0.1), collection)
    else:
        tapis.scale = (scale_factor, scale_factor, 1.0)
        tapis.hide_viewport = True
        tapis.hide_render = True
        tapis.display_type = 'WIRE'

    montagne = placer_objet_fixe("terrain", collection=collection, position=(cx, cy, cz))
    if montagne:
        montagne.scale = (scale_factor, scale_factor, scale_factor)

    loc_palais = (cx, cy, cz + 12.0) 
    placer_objet_fixe("maison_shogun", collection=collection, position=loc_palais, echelle=(1.5,1.5,1.5))
    
    
    loc_temple = (cx, cy - 13.0, cz)
    loc_temple_ringo = (cx+15, cy +45, cz+1)
    

    placer_objet_fixe("temple", collection=collection, position=loc_temple, rotation=(0.0, 0.0, 0.0), echelle=(1.5, 1.5, 1.5))


    # ==========================================
    #LE PONT LES TORIS
    # ==========================================

    rotation_pont = (0.0, 0.0, math.radians(90))

    # Le Pont 
    loc_pont = (cx, cy + 13.0, cz + 1.8)
    placer_objet_fixe("pont", collection=collection, position=loc_pont, rotation=rotation_pont, echelle=(1.5,1.3,2))
    
    # Les Toris (Montés à cz + 1.0, écartés pour encadrer le grand pont, échelle boostée à 1.8)
    loc_tori_gauche = (cx - 8, cy + 13.0, cz + 2)
    loc_tori_droit = (cx + 8, cy + 13.0, cz + 2)
    
    rotation_tori= (0.0, 0.0, math.radians(180))
    
    placer_objet_fixe("tori", collection=collection, position=loc_tori_gauche, rotation=rotation_tori, echelle=(1.5, 1.5, 1.5))
    placer_objet_fixe("tori", collection=collection, position=loc_tori_droit, rotation=rotation_tori,echelle=(1.5, 1.5, 1.5))

    loc_grand_arbre = (cx, cy + 18.0, cz+12)
    rotation_arbre= (0.0, 0.0, math.radians(-90))
    placer_objet_fixe("grand_arbre", collection=collection, position=loc_grand_arbre,rotation= rotation_arbre, echelle=(1,1,1))
    
    
    
    # ==========================================
    # LA PLUIE DE SAKURA
    # ==========================================
    # On se place au-dessus du centre de l'île, à 30 mètres de haut
    loc_pluie = (cx, cy, cz + 30.0)
    loc_turbulence = (cx, cy, cz + 25.0)
    loc_vent = (cx, cy+20, cz + 34.0)
    rotation_vent= (math.radians(135), 0.0, 0)
    # 1. On place le Plane (qui contient les particules) et on l'agrandit pour couvrir l'île
    placer_objet_fixe("Plane_sakura", collection=collection, position=loc_pluie, echelle=(15,15,1))
    
    
    plane = bpy.data.objects.get("Plane_sakura")
    
    mat_invis = bpy.data.materials.new(name="Mat_Nuage_Invisible")
    mat_invis.use_nodes = True
    mat_invis.blend_method = 'CLIP' # Mode de transparence pour Eevee
    mat_invis.diffuse_color = (0, 0, 0, 0) # Alpha à zéro

    n_nodes = mat_invis.node_tree.nodes
    n_links = mat_invis.node_tree.links
    for n in n_nodes: n_nodes.remove(n)
    
    n_out = n_nodes.new('ShaderNodeOutputMaterial')
    n_transp = n_nodes.new('ShaderNodeBsdfTransparent') 
    n_links.new(n_transp.outputs['BSDF'], n_out.inputs['Surface'])

    plane.data.materials.append(mat_invis)
    

    # 2. On place le vent exactement au même endroit
    placer_objet_fixe("Wind_sakura", collection=collection, rotation =rotation_vent, position=loc_vent, echelle=(5,5,1))
    
     # 3. On place le vent exactement au même endroit
    placer_objet_fixe("turbulence_sakura", collection=collection, position=loc_turbulence,echelle=(5,5,1))

    # 🛡️ LES ZONES INTERDITES
    positions_memoire.append({"loc": Vector(loc_palais), "radius": 4.0})
    positions_memoire.append({"loc": Vector(loc_pont), "radius": 6.0}) # Sécurité élargie pour le gros pont
    positions_memoire.append({"loc": Vector(loc_tori_gauche), "radius": 3.0})
    positions_memoire.append({"loc": Vector(loc_tori_droit), "radius": 3.0})
    
    return tapis
# ==========================================
#  L'ASSEMBLAGE FINAL
# ==========================================

def generer_capitale(nom_ile, centre_ile, rayon_plateau, nb_maisons=50, nb_arbres=40):
    nom_dossier = "VILLE_CAPITALE"

    if nom_dossier in bpy.data.collections:
        col = bpy.data.collections[nom_dossier]
        for obj in col.objects: bpy.data.objects.remove(obj, do_unlink=True)
    else:
        col = bpy.data.collections.new(nom_dossier)
        bpy.context.scene.collection.children.link(col)

    bprint("🚀 DÉMARRAGE DE L'ASSEMBLAGE DE LA CAPITALE...")
    positions_memoire = []

    # 🌟 LES DEUX LIGNES MAGIQUES SONT ICI :
    sculpter_ile_capitale(nom_ile)
    appliquer_materiel_capitale(nom_ile)

    # ÉTAPE 1 : On place ton décor et on récupère le Tapis (manuel ou automatique) !
    tapis_spawn = placer_decor_custom(col, centre_ile, rayon_plateau, positions_memoire)

    if not tapis_spawn:
        bprint("❌ ERREUR : Aucun tapis de spawn n'a pu être généré !")
        return

    # ÉTAPE 2 : La Génération Aléatoire
    noms_maisons = ["maison_pauvre", "maison_riche"] 

    total_maisons = generer_maisons(nb_maisons, noms_maisons, tapis_spawn.name, col, positions_memoire)
    bprint(f"🏠 Maisons posées : {total_maisons}/{nb_maisons}")

    total_arbres = generer_arbres(nb_arbres, "arbre", tapis_spawn.name, col, positions_memoire)
    bprint(f"🌳 Arbres posés : {total_arbres}/{nb_arbres}")

    bprint("✅ Capitale des Fleurs complètement assemblée !")




# ==========================================
# 👇 EXÉCUTION
# ==========================================





