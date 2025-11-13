import re
from typing import Dict, List, Tuple, Optional

class FiltroGroserias:
    def __init__(self):
        self.palabras_prohibidas = {
            'pendejo', 'pendeja', 'estupido', 'estupida', 'idiota', 'imbecil',
            'cabron', 'pendejos', 'estupidos', 'estupidas', 'idiotas', 'imbeciles',
            'maldito', 'maldita', 'verga', 'puto', 'puta', 'pinche', 'chinga',
            'chingar', 'carajo', 'mierda', 'cagon', 'culero', 'joder', 'coño',
            'hostia', 'gilipollas', 'capullo', 'subnormal', 'retrasado', 'mamón',
            'zoquete', 'cenutrio', 'anormal', 'tarado', 'memo', 'lelo', 'bobo',
            'tonto', 'necio', 'ignorante', 'patán', 'gili', 'pringao', 'mameluco',
            'piltrafa', 'desgraciado', 'malnacido', 'sinvergüenza', 'canalla',
            'granuja', 'bellaco', 'pícaro', 'fullero', 'tramposo', 'embustero',
            'mentiroso', 'farsante', 'charlatán', 'estafador', 'ladrón', 'ratero',
            'caco', 'chorizo', 'golfante', 'tunante', 'bribón', 'pillo', 'malhechor',
            'delincuente', 'criminal', 'bandido', 'forajido', 'faccioso', 'rebelde',
            'sedicioso', 'amotinado', 'insurrecto', 'alzado', 'revoltoso', 'perturbador',
            'alterador', 'desordenado', 'anárquico', 'caótico', 'confuso', 'tumultuoso',
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
            'picotazo', 'dentellada', 'tarascada', 'mascada', 'masticación', 'trituración',
            'molienda', 'machacamiento', 'aplastamiento', 'compresión', 'presión',
            'apretón', 'estrujón', 'exprimido', 'estrujado', 'comprimido', 'compactado',
            'densificado', 'condensado', 'concentrado', 'reducido', 'disminuido',
            'aminorado', 'atenuado', 'mitigado', 'palizado', 'cachetes', 'hijo', 'perra'
        }
        
        self.patrones_evasion = [
            (r'(.)\1{2,}', r'\1'), 
            (r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', ''),  
            (r'\s+', ' '), 
        ]
        
        self.variaciones = {
            'estupido': ['estupid', 'estupidoo', 'estupidooo'],
            'pendejo': ['pendej', 'pendej0', 'p3ndejo'],
        }

    def normalizar_texto(self, texto: str) -> str:
        if not texto:
            return ""
            
        texto_normalizado = texto.lower().strip()
        
        for patron, reemplazo in self.patrones_evasion:
            texto_normalizado = re.sub(patron, reemplazo, texto_normalizado)
        
        for palabra_base, variaciones in self.variaciones.items():
            for variacion in variaciones:
                if variacion in texto_normalizado:
                    texto_normalizado = texto_normalizado.replace(variacion, palabra_base)
        
        return texto_normalizado

    def contiene_groserias(self, texto: str) -> Tuple[bool, List[str]]:
        if not texto or not isinstance(texto, str):
            return False, []
        
        texto_normalizado = self.normalizar_texto(texto)
        palabras_encontradas = []
        
        palabras = re.findall(r'\b\w+\b', texto_normalizado)
        
        for palabra in palabras:
            if palabra in self.palabras_prohibidas:
                palabras_encontradas.append(palabra)
        
        return len(palabras_encontradas) > 0, palabras_encontradas

    def filtrar_texto(self, texto: str, reemplazo: str = "***") -> str:
        if not texto:
            return texto
            
        texto_filtrado = texto
        texto_normalizado = self.normalizar_texto(texto)
        
        palabras = re.findall(r'\b\w+\b', texto_normalizado)
        
        for palabra in palabras:
            if palabra in self.palabras_prohibidas:
                patron = re.compile(re.escape(palabra), re.IGNORECASE)
                texto_filtrado = patron.sub(reemplazo, texto_filtrado)
        
        return texto_filtrado

    def verificar_campos(self, diccionario_campos: Dict) -> Tuple[bool, Optional[str], List[str]]:
        todos_los_textos = []
        
        for campo, valor in diccionario_campos.items():
            if valor is not None:
                todos_los_textos.append(str(valor))
        
        texto_completo = " ".join(todos_los_textos)
        contiene, palabras_encontradas = self.contiene_groserias(texto_completo)
        
        if contiene:
            for campo, valor in diccionario_campos.items():
                if valor and self.contiene_groserias(str(valor))[0]:
                    return True, campo, palabras_encontradas
        
        return False, None, palabras_encontradas

    def es_texto_apropiado(self, texto: str) -> bool:
        contiene, _ = self.contiene_groserias(texto)
        return not contiene


def contiene_groserias(texto):

    filtro = FiltroGroserias()
    return filtro.contiene_groserias(texto)[0]

def verificar_campos(diccionario_campos):
    filtro = FiltroGroserias()
    resultado, campo, _ = filtro.verificar_campos(diccionario_campos)
    return resultado, campo


filtro_groserias = FiltroGroserias()