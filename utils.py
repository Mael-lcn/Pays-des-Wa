import bpy



# RAZ ou créer le loggeur
if "Wano_Console" not in bpy.data.texts:
    bpy.data.texts.new("Wano_Console")
else:
    bpy.data.texts["Wano_Console"].clear()



def bprint(*args):
    """Affiche les messages dans un onglet texte de Blender au lieu de la console invisible"""
    message = " ".join(str(a) for a in args)
    # Écrit le message dedans
    console = bpy.data.texts["Wano_Console"]
    console.write(message + "\n")



def hex_to_rgba(hex_str):
        hex_str = hex_str.lstrip('#')
        r, g, b = tuple(int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        return (r**2.2, g**2.2, b**2.2, 1.0)
