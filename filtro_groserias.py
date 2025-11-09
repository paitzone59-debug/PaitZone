# filtro_groserias.py

PALABRAS_PROHIBIDAS = {
    'pendejo', 'pendeja', 'estupido', 'estupida', 'idiota', 'imbecil',
    'cabron', 'pendejos', 'estupidos', 'estupidas', 'idiotas', 'imbeciles',
    'maldito', 'maldita', 'verga', 'puto', 'puta', 'pinche', 'chinga',
    'chingar', 'carajo', 'mierda', 'cagon', 'culero', 'puto', 'puta',
    'joder', 'coño', 'hostia', 'gilipollas', 'capullo', 'subnormal',
    'retrasado', 'mamón', 'zoquete', 'cenutrio', 'anormal', 'tarado',
    'memo', 'lelo', 'bobo', 'tonto', 'necio', 'ignorante', 'patán',
    'gili', 'pringao', 'mameluco', 'piltrafa', 'desgraciado', 'malnacido',
    'sinvergüenza', 'canalla', 'granuja', 'bellaco', 'pícaro', 'fullero',
    'tramposo', 'embustero', 'mentiroso', 'farsante', 'charlatán', 'estafador',
    'ladrón', 'ratero', 'caco', 'chorizo', 'golfante', 'pícaro', 'tunante',
    'bribón', 'pillo', 'granuja', 'bellaco', 'malhechor', 'delincuente',
    'criminal', 'bandido', 'forajido', 'faccioso', 'rebelde', 'sedicioso',
    'amotinado', 'insurrecto', 'alzado', 'revoltoso', 'perturbador', 'alterador',
    'desordenado', 'anárquico', 'caótico', 'confuso', 'revoltoso', 'tumultuoso',
    'aluvional', 'desbordado', 'inundado', 'anegado', 'inmerso', 'sumergido',
    'ahogado', 'asfixiado', 'sofocado', 'estrangular', 'suicidar', 'matar',
    'asesinar', 'eliminar', 'exterminar', 'aniquilar', 'destruir', 'arrasar',
    'devastar', 'asolar', 'destrozar', 'destripar', 'descuartizar', 'despedazar',
    'mutilado', 'amputado', 'cercenado', 'truncado', 'cortado', 'seccionado',
    'dividido', 'partido', 'fracturado', 'quebrado', 'roto', 'resquebrajado',
    'agrietado', 'hendido', 'rajado', 'cuarteado', 'astillado', 'desgarrado',
    'rasgado', 'desgarrón', 'rasgón', 'rotura', 'fractura', 'quebradura',
    'grieta', 'hendidura', 'raja', 'cuarteadura', 'astilla', 'desgarro',
    'rasgadura', 'desgarramiento', 'rasguño', 'arañazo', 'rayón', 'mella',
    'melladura', 'mordisco', 'mordedura', 'picadura', 'punzada', 'pinchazo',
    'picotazo', 'mordisco', 'mordedura', 'dentellada', 'tarascada', 'mascada',
    'masticación', 'trituración', 'molienda', 'machacamiento', 'aplastamiento',
    'compresión', 'presión', 'apretón', 'estrujón', 'exprimido', 'estrujado',
    'comprimido', 'compactado', 'densificado', 'condensado', 'concentrado',
    'reducido', 'disminuido', 'aminorado', 'atenuado', 'mitigado', 'palizado',
    'cachetes', 'hijo', 'perra'
}

def contiene_groserias(texto):
    """Verifica si el texto contiene palabras prohibidas"""
    if not texto or not isinstance(texto, str):
        return False
    
    texto_limpio = texto.lower().strip()
    
    if not texto_limpio:
        return False
    
    palabras = texto_limpio.split()
    
    for palabra in palabras:
        palabra_limpia = palabra.strip('.,!?;:"()[]{}')
        
        if palabra_limpia in PALABRAS_PROHIBIDAS:
            return True
            
    return False

def verificar_campos(diccionario_campos):
    """Verifica múltiples campos de un formulario"""
    for campo, valor in diccionario_campos.items():
        if contiene_groserias(str(valor)):
            return True, campo
    return False, None