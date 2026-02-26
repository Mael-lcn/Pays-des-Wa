import bpy
import math
import importlib
import utils
importlib.reload(utils)
from utils import hex_to_rgba

def sculpter_ile_udon(nom_ile):

    ile = bpy.data.objects.get(nom_ile)
    if not ile: return

    scale_z = ile.scale[2]
    
    for v in ile.data.vertices:
        if abs(v.co.z) < 0.001 or v.co.z > 0.0:
            x, y = v.co.x, v.co.y
            
            z_val = 4.0 
            dist_centre = math.hypot(x, y)
            
            # TOUR CENTRALE 
            if dist_centre < 8.0: # Rayon augmenté pour plus de largeur
                # La courbe irait jusqu'à 25m, mais on la "coupe" à 16m pour faire un plateau plat
                courbe = math.cos(dist_centre / 8.0 * (math.pi / 2)) * 25.0
                hauteur = min(courbe, 16.0) 
                z_val = max(z_val, 4.0 + hauteur)
            
            # LES 6 AUTRES TRUCS 
            for i in range(6):
                angle = i * (math.pi / 3) 
                px = math.cos(angle) * 11.0 # Poussées plus loin
                py = math.sin(angle) * 11.0
                dist_fosse = math.hypot(x - px, y - py)
                
                if dist_fosse < 5.5:
                    creux = math.cos(dist_fosse / 5.5 * (math.pi / 2)) * 6.0
                    z_val -= creux 
                    
            # LES 6 PILIERS EXTÉRIEURS (Plus excentrés, sommets plats)
            for i in range(6):
                angle = i * (math.pi / 3) + (math.pi / 6) 
                px = math.cos(angle) * 16.5 # Fortement excentrés vers les bords
                py = math.sin(angle) * 16.5
                dist_pilier = math.hypot(x - px, y - py)
                
                if dist_pilier < 4.5:
                    # Même astuce : on coupe la pointe pour faire un sommet plat
                    courbe = math.cos(dist_pilier / 4.5 * (math.pi / 2)) * 20.0
                    hauteur = min(courbe, 13.0) 
                    z_val = max(z_val, 4.0 + hauteur)
                    
            v.co.z = max(-1.0, z_val) / scale_z
            
    ile.data.update()
    
    
def appliquer_materiel_udon(nom_ile):

    ile = bpy.data.objects.get(nom_ile)
    if not ile: return


    mat_name = f"Mat_{nom_ile}_Udon"
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        
    ile.data.materials.clear()
    ile.data.materials.append(mat)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # --- NOEUDS DE BASE ---
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (800, 0)
    
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.location = (500, 0)
    principled.inputs['Roughness'].default_value = 0.95 
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    # 🎯 CORRECTION 1 : On prend les coordonnées Locales (Object) !
    coord = nodes.new('ShaderNodeTexCoord')
    coord.location = (-1000, 0)
    
    sep_xyz = nodes.new('ShaderNodeSeparateXYZ')
    sep_xyz.location = (-800, -200)
    links.new(coord.outputs['Object'], sep_xyz.inputs['Vector'])

    # ==========================================
    # 🎨 1. LA GESTION DES COULEURS
    # ==========================================
    noise_montagne = nodes.new('ShaderNodeTexNoise')
    noise_montagne.location = (-600, 200)
    noise_montagne.inputs['Scale'].default_value = 8.0
    links.new(coord.outputs['Object'], noise_montagne.inputs['Vector'])

    mix_montagne = nodes.new('ShaderNodeMixRGB')
    mix_montagne.location = (-400, 200)
    mix_montagne.inputs[1].default_value = hex_to_rgba('#b5b2a8') # Gris cendre
    mix_montagne.inputs[2].default_value = hex_to_rgba('#8f8c83') # Gris cendre sombre
    links.new(noise_montagne.outputs['Fac'], mix_montagne.inputs['Fac'])

    # 🎯 CORRECTION 2 : Ajustement des hauteurs pour les coordonnées locales
    map_z = nodes.new('ShaderNodeMapRange')
    map_z.location = (-400, 0)
    map_z.inputs[1].default_value = 5.0  # Sol plat (Terre)
    map_z.inputs[2].default_value = 7.5  # Début des pentes (Roche)
    links.new(sep_xyz.outputs['Z'], map_z.inputs['Value'])

    mix_final = nodes.new('ShaderNodeMixRGB')
    mix_final.location = (-150, 100)
    mix_final.inputs[1].default_value = hex_to_rgba('#84714f') # Terre sombre
    links.new(map_z.outputs['Result'], mix_final.inputs['Fac'])
    links.new(mix_montagne.outputs['Color'], mix_final.inputs[2])
    
    links.new(mix_final.outputs['Color'], principled.inputs['Base Color'])

    # ==========================================
    # LE RELIEF
    # ==========================================
    noise_bump = nodes.new('ShaderNodeTexNoise')
    noise_bump.location = (-300, -300)
    noise_bump.inputs['Scale'].default_value = 25.0 
    noise_bump.inputs['Detail'].default_value = 5.0
    links.new(coord.outputs['Object'], noise_bump.inputs['Vector'])

    bump = nodes.new('ShaderNodeBump')
    bump.location = (0, -300)
    bump.inputs['Strength'].default_value = 0.25 
    bump.inputs['Distance'].default_value = 0.5
    links.new(noise_bump.outputs['Fac'], bump.inputs['Height'])
    
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    
    
    

def generer_udon(nom_ile, centre_ile=None, rayon_plateau=None):
    """ Chef d'orchestre pour la construction de la prison d'Udon """
    print(f"🏭 Génération de la région d'Udon sur {nom_ile}...")
    
    sculpter_ile_udon(nom_ile)
    appliquer_materiel_udon(nom_ile)
    
    
    print(f"✅ Udon ({nom_ile}) est terminée !")