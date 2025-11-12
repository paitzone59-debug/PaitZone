import re
from pathlib import Path
from bs4 import BeautifulSoup, Comment
import os

import shutil
from datetime import datetime

def hacer_backup(archivos):
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir)
    for archivo in archivos:
        if Path(archivo).exists():
            shutil.copy2(archivo, backup_dir)
    print(f"📦 Backup creado en: {backup_dir}")
    
class LimpiadorCompleto:
    def __init__(self):
        self.archivos_procesados = 0
        
    def limpiar_html(self, contenido):
        """Limpia archivos HTML usando BeautifulSoup (más preciso)"""
        try:
            soup = BeautifulSoup(contenido, 'html.parser')
            
            # Eliminar todos los comentarios HTML
            comentarios = soup.find_all(string=lambda text: isinstance(text, Comment))
            for comentario in comentarios:
                comentario.extract()
            
            # Convertir a string y limpiar formato
            contenido_limpio = str(soup)
            contenido_limpio = re.sub(r'\n\s*\n', '\n', contenido_limpio)  # Líneas vacías múltiples
            contenido_limpio = re.sub(r'[^\x00-\x7F]+', '', contenido_limpio)  # Emojis
            
            return contenido_limpio.strip()
        except Exception as e:
            print(f"⚠️  Error con BeautifulSoup, usando regex: {e}")
            # Fallback a regex si BeautifulSoup falla
            contenido = re.sub(r'<!--.*?-->', '', contenido, flags=re.DOTALL)
            contenido = re.sub(r'[^\x00-\x7F]+', '', contenido)
            return contenido.strip()
    
    def limpiar_python(self, contenido):
        """Limpia archivos Python eliminando comentarios y emojis"""
        lineas_limpias = []
        
        for linea in contenido.split('\n'):
            # Eliminar comentarios (pero preservar shebang y encoding)
            if linea.strip().startswith(('#!', '# -*-')):
                lineas_limpias.append(linea)
                continue
                
            # Eliminar comentarios al final de la línea
            linea_limpia = re.sub(r'\s*#.*$', '', linea)
            
            # Solo agregar si la línea no está vacía después de quitar comentarios
            if linea_limpia.strip():
                lineas_limpias.append(linea_limpia)
        
        contenido_limpio = '\n'.join(lineas_limpias)
        # Eliminar emojis y caracteres no ASCII
        contenido_limpio = re.sub(r'[^\x00-\x7F]+', '', contenido_limpio)
        
        return contenido_limpio.strip()
    
    def procesar_archivo(self, ruta_archivo):
        """Procesa un archivo individual"""
        archivo = Path(ruta_archivo)
        
        if not archivo.exists():
            print(f"❌ Archivo no encontrado: {ruta_archivo}")
            return False
        
        try:
            # Leer contenido
            contenido = archivo.read_text(encoding='utf-8', errors='ignore')
            
            # Determinar tipo y limpiar
            if archivo.suffix.lower() in ['.html', '.htm']:
                print(f"🔄 Procesando HTML: {archivo.name}")
                contenido_limpio = self.limpiar_html(contenido)
            elif archivo.suffix.lower() == '.py':
                print(f"🔄 Procesando Python: {archivo.name}")
                contenido_limpio = self.limpiar_python(contenido)
            else:
                print(f"⚠️  Formato no soportado: {archivo.name}")
                return False
            
            # Guardar archivo limpio (SOBREESCRIBE el original)
            archivo.write_text(contenido_limpio, encoding='utf-8')
            self.archivos_procesados += 1
            print(f"✅ Limpiado: {archivo.name}")
            return True
            
        except Exception as e:
            print(f"❌ Error procesando {archivo.name}: {e}")
            return False
    
    def procesar_lista(self, lista_archivos):
        """Procesa una lista de archivos"""
        print("🚀 INICIANDO LIMPIEZA DE ARCHIVOS...")
        print("=" * 50)
        
        for archivo in lista_archivos:
            self.procesar_archivo(archivo)
        
        print("=" * 50)
        print(f"🎉 LIMPIEZA COMPLETADA: {self.archivos_procesados} archivos procesados")

def main():
    # TU LISTA DE ARCHIVOS - ACTUALIZADA
    archivos_a_limpiar = [
        "_notificaciones.html",
        "admin_equipos.html", 
        "admin_usuarios.html",
        "admin.html",
        "agregar_usuario.html",
        "base.html",
        "chat_equipo.html",
        "create_project.html",
        "editar_perfil.html",
        "inicio.html",
        "login.html",
        "mi_equipo.html",
        "perfil.html",
        "project.html",
        "register.html",
        "terminos_y_condiciones.html",
        "app.py"
    ]
    
    # Verificar qué archivos existen
    archivos_existentes = []
    archivos_no_encontrados = []
    
    for archivo in archivos_a_limpiar:
        if Path(archivo).exists():
            archivos_existentes.append(archivo)
        else:
            archivos_no_encontrados.append(archivo)
    
    print("📁 ARCHIVOS ENCONTRADOS (" + str(len(archivos_existentes)) + "):")
    for archivo in archivos_existentes:
        print(f"   ✅ {archivo}")
    
    if archivos_no_encontrados:
        print("\n⚠️  ARCHIVOS NO ENCONTRADOS (" + str(len(archivos_no_encontrados)) + "):")
        for archivo in archivos_no_encontrados:
            print(f"   ❌ {archivo}")
    
    if not archivos_existentes:
        print("❌ No se encontraron archivos para procesar")
        return
    
    # Mostrar resumen
    print(f"\n📊 RESUMEN:")
    print(f"   • Total de archivos en lista: {len(archivos_a_limpiar)}")
    print(f"   • Archivos encontrados: {len(archivos_existentes)}")
    print(f"   • Archivos no encontrados: {len(archivos_no_encontrados)}")
    
    # Confirmación
    confirmacion = input("\n¿Continuar con la limpieza? (s/n): ").lower()
    if confirmacion != 's':
        print("❌ Operación cancelada")
        return
    
    # Procesar archivos
    limpiador = LimpiadorCompleto()
    limpiador.procesar_lista(archivos_existentes)
    
    # Mensaje final
    print(f"\n✨ Todos los archivos han sido limpiados exitosamente!")
    print("   Los comentarios y emojis han sido eliminados.")

if __name__ == "__main__":
    main()