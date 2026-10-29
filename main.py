from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform
from kivy.clock import Clock
import datetime
import time
import threading
import json
import os
import re

# Importación segura de pyttsx3 y reconocimiento de voz
try:
    import pyttsx3
    import pythoncom
except ImportError:
    pyttsx3 = None
    pythoncom = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

class MemoriaJarvisAutonoma:
    """Clase interna para gestionar la persistencia local de datos sin archivos externos"""
    def __init__(self, archivo="jarvis_memoria.json"):
        self.archivo = archivo
        self.datos = self.cargar_datos()

    def cargar_datos(self):
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def guardar_dato(self, clave, valor):
        self.datos[clave] = valor
        try:
            with open(self.archivo, "w", encoding="utf-8") as f:
                json.dump(self.datos, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar memoria: {e}")

    def obtener_dato(self, clave):
        return self.datos.get(clave, None)

class JarvisInterface(BoxLayout):
    def __init__(self, **kwargs):
        super(JarvisInterface, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10
        self.modo_operativo = None
        self.escuchando_activo = True
        self.sistema_activo = True

        # Variables tácticas
        self.ultimo_calculo = "Sin registros previos."
        self.cronometro_inicio = None
        self.linterna_encendida = False
        self.libreta_notas = []

        # Variables para captura e interacción de notificaciones
        self.ultima_notificacion = None
        self.esperando_confirmacion_lectura = False

        # Inicializar memoria autónoma y voz
        self.memoria = MemoriaJarvisAutonoma()
        self.inicializar_voz()

        # Área de Historial de Conversación
        self.chat_history = Label(
            text="[J.A.R.V.I.S. - Núcleo Táctico Autónomo Activo]\n",
            size_hint_y=None,
            halign='left',
            valign='top',
            markup=True
        )
        self.chat_history.bind(texture_size=self.chat_history.setter('size'))

        scroll = ScrollView(size_hint=(1, 0.7))
        scroll.add_widget(self.chat_history)
        self.add_widget(scroll)

        # Campo de Entrada de Texto
        self.user_input = TextInput(
            hint_text='Escribe un comando o di "Jarvis..."',
            size_hint=(1, 0.15),
            multiline=False
        )
        self.user_input.bind(on_text_validate=self.enviar_comando_texto)
        self.add_widget(self.user_input)

        # Botón de Envío de Texto
        self.send_button = Button(
            text='Enviar Comando Táctico',
            size_hint=(1, 0.15),
            background_color=(0.1, 0.6, 0.8, 1)
        )
        self.send_button.bind(on_press=self.enviar_comando_texto)
        self.add_widget(self.send_button)

        # Iniciar escucha continua en segundo plano
        threading.Thread(target=self.bucle_escucha_continua, daemon=True).start()

    def inicializar_voz(self):
        self.engine_ok = False
        if pyttsx3:
            try:
                self.engine_ok = True
            except Exception as e:
                print(f"Aviso de voz: {e}")

    def hablar(self, texto):
        if self.engine_ok and pyttsx3:
            def tarea_voz():
                try:
                    if pythoncom:
                        pythoncom.CoInitialize()
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 175)
                    engine.say(texto)
                    engine.runAndWait()
                    if pythoncom:
                        pythoncom.CoUninitialize()
                except Exception as e:
                    print(f"Error al reproducir voz: {e}")
            threading.Thread(target=tarea_voz, daemon=True).start()

    def bucle_escucha_continua(self):
        if not sr:
            return
        
        recognizer = sr.Recognizer()
        while self.escuchando_activo:
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    audio = recognizer.listen(source, timeout=None, phrase_time_limit=8)
                    texto_reconocido = recognizer.recognize_google(audio, language="es-ES").lower()
                    
                    if "jarvis" in texto_reconocido or self.esperando_confirmacion_lectura:
                        if not self.sistema_activo:
                            if "jarvis" in texto_reconocido:
                                self.sistema_activo = True
                                resp = "Aca estoy señor."
                                Clock.schedule_once(lambda dt: self.actualizar_chat_sistema(texto_reconocido, resp), 0)
                            continue

                        if any(w in texto_reconocido for w in ["es todo", "descansa", "silencio", "duérmete"]):
                            self.sistema_activo = False
                            self.esperando_confirmacion_lectura = False
                            resp = "Entendido, señor."
                            Clock.schedule_once(lambda dt: self.actualizar_chat_sistema(texto_reconocido, resp), 0)
                            continue

                        comando_real = texto_reconocido.replace("jarvis", "").strip() if "jarvis" in texto_reconocido else texto_reconocido.strip()
                        if comando_real:
                            Clock.schedule_once(lambda dt, cmd=comando_real: self.procesar_comando_voz_directo(cmd), 0)
            except Exception:
                continue

    def actualizar_chat_sistema(self, voz, respuesta):
        self.chat_history.text += f"\n[Voz]: {voz}\n[J.A.R.V.I.S.]: {respuesta}"
        self.hablar(respuesta)

    def procesar_comando_voz_directo(self, texto):
        self.chat_history.text += f"\n[Voz (Manos Libres)]: {texto}"
        respuesta = self.procesar_logica_jarvis(texto)
        self.chat_history.text += f"\n[J.A.R.V.I.S.]: {respuesta}"
        self.hablar(respuesta)

    def enviar_comando_texto(self, instance):
        texto = self.user_input.text.strip()
        if not texto:
            return

        self.chat_history.text += f"\n[Tú]: {texto}"
        self.user_input.text = ""

        respuesta = self.procesar_logica_jarvis(texto)
        self.chat_history.text += f"\n[J.A.R.V.I.S.]: {respuesta}"
        self.hablar(respuesta)

    def simular_notificacion_entrante(self, app_origen, remitente, texto_contenido):
        self.ultima_notificacion = {
            'app': app_origen,
            'remitente': remitente,
            'texto': texto_contenido
        }
        self.esperando_confirmacion_lectura = True
        alerta = f"Señor, notificación de {app_origen} de {remitente}. ¿Desea que la lea?"
        self.chat_history.text += f"\n[J.A.R.V.I.S. ALERTA]: {alerta}"
        self.hablar(alerta)

    def procesar_logica_jarvis(self, comando):
        comando_lower = comando.lower()

        if self.esperando_confirmacion_lectura:
            if any(w in comando_lower for w in ["sí", "si", "léela", "leela", "lee", "claro", "por favor"]):
                self.esperando_confirmacion_lectura = False
                if self.ultima_notificacion:
                    contenido = self.ultima_notificacion['texto']
                    self.ultima_notificacion = None
                    return f"Mensaje: {contenido}"
                return "No hay mensajes pendientes."

            elif any(w in comando_lower for w in ["no", "mejor no", "cancelar", "ignora", "omitir", "solo no"]):
                self.esperando_confirmacion_lectura = False
                self.ultima_notificacion = None
                return "Entendido, señor."

        if any(p in comando_lower for p in ["hola", "saludos", "buenos días", "buenas tardes"]):
            nombre = self.memoria.obtener_dato("nombre_usuario")
            if nombre:
                return f"Hola, {nombre}. ¿Qué sistemas deseas revisar?"
            return "Sistemas en línea. ¿Cómo te llamas?"

        elif "mi nombre es" in comando_lower:
            nombre = comando.split("mi nombre es")[-1].strip().capitalize()
            self.memoria.guardar_dato("nombre_usuario", nombre)
            return f"Registrado, {nombre}."

        elif "cómo me llamo" in comando_lower or "quién soy" in comando_lower:
            nombre = self.memoria.obtener_dato("nombre_usuario")
            if nombre:
                return f"Te llamas {nombre}."
            return "Aún no tengo registrado tu nombre."

        elif "hora" in comando_lower:
            ahora = datetime.datetime.now().strftime("%H:%M:%S")
            return f"Son las {ahora}."
        elif "fecha" in comando_lower or "día es" in comando_lower:
            hoy = datetime.date.today().strftime("%d/%m/%Y")
            return f"Hoy es {hoy}."

        elif "batería" in comando_lower or "bateria" in comando_lower or "estado del sistema" in comando_lower:
            return self.obtener_estado_bateria()

        elif "anota" in comando_lower or "apunta" in comando_lower or "nota" in comando_lower:
            if "lee" in comando_lower or "muéstrame" in comando_lower or "muestra" in comando_lower:
                if self.libreta_notas:
                    notas_str = ". ".join(self.libreta_notas)
                    return f"Notas guardadas: {notas_str}"
                return "La libreta de campo está vacía."
            else:
                nota_texto = comando_lower.replace("anota", "").replace("apunta", "").replace("jarvis", "").strip()
                if nota_texto:
                    self.libreta_notas.append(nota_texto)
                    return "Nota guardada en libreta de campo."
                return "Indica qué deseas anotar."

        elif "último cálculo" in comando_lower or "ultimo calculo" in comando_lower or "resultado anterior" in comando_lower:
            return f"El último cálculo registrado es: {self.ultimo_calculo}"

        elif "inicia cronómetro" in comando_lower or "inicia cronometro" in comando_lower or ("cronómetro" in comando_lower and "iniciar" in comando_lower):
            self.cronometro_inicio = time.time()
            return "Cronómetro iniciado."
        elif "cuánto tiempo" in comando_lower or "cuanto tiempo" in comando_lower or "tiempo transcurrido" in comando_lower:
            if self.cronometro_inicio:
                transcurrido = int(time.time() - self.cronometro_inicio)
                mins, segs = divmod(transcurrido, 60)
                return f"Tiempo transcurrido: {mins} minutos y {segs} segundos."
            return "El cronómetro no ha sido iniciado."
        elif "detén cronómetro" in comando_lower or "deten cronometro" in comando_lower or "para cronómetro" in comando_lower:
            if self.cronometro_inicio:
                transcurrido = int(time.time() - self.cronometro_inicio)
                self.cronometro_inicio = None
                mins, segs = divmod(transcurrido, 60)
                return f"Cronómetro detenido. Tiempo total: {mins} minutos y {segs} segundos."
            return "No hay cronómetro activo."

        elif "linterna" in comando_lower or "flash" in comando_lower or "luz" in comando_lower:
            accion = "apaga" if "apaga" in comando_lower or "apagar" in comando_lower else "enciende"
            return self.controlar_linterna(accion)

        elif "llama a" in comando_lower or "marcar a" in comando_lower or "llamar a" in comando_lower:
            limpio = comando_lower.replace("jarvis", "").replace("por favor", "").strip()
            destino = limpio.replace("llama a", "").replace("llamar a", "").replace("marcar a", "").strip()
            return self.ejecutar_llamada(destino)

        elif "cancelar" in comando_lower or "reiniciar" in comando_lower:
            self.modo_operativo = None
            self.esperando_confirmacion_lectura = False
            return "Operación cancelada. En espera."

        elif "friccion" in comando_lower or "fricción" in comando_lower or self.modo_operativo == "friccion":
            try:
                if "friccion" in comando_lower and not any(char.isdigit() for char in comando_lower):
                    self.modo_operativo = "friccion"
                    return "Módulo hidráulico activado. Indica diámetro, caudal y longitud."

                coeficiente = 24.0
                if "2.5" in comando_lower or "2 y media" in comando_lower or "dos y media" in comando_lower:
                    coeficiente = 2.0
                elif "1.5" in comando_lower or "1 y media" in comando_lower or "una y media" in comando_lower:
                    coeficiente = 24.0

                match_q = re.search(r'(\d+\.?\d*)\s*(?:gpm|galones|gal|lpm)', comando_lower)
                match_l = re.search(r'(\d+\.?\d*)\s*(?:pies|ft|metros|m)', comando_lower)
                
                numeros = [float(n) for n in re.findall(r'\d+\.?\d*', comando)]
                nums_filtrados = [n for n in numeros if n not in [1, 2, 1.5, 2.5]]

                q = float(match_q.group(1)) if match_q else (nums_filtrados[0] if len(nums_filtrados) > 0 else 0)
                l = float(match_l.group(1)) if match_l else (nums_filtrados[1] if len(nums_filtrados) > 1 else 0)

                if q > 0 and l > 0:
                    fl = coeficiente * ((q / 100.0) ** 2) * (l / 100.0)
                    resultado_str = f"Pérdida de fricción: {fl:.2f} PSI."
                    self.ultimo_calculo = resultado_str
                    self.modo_operativo = None
                    return resultado_str
                else:
                    self.modo_operativo = "friccion"
                    return "Indica diámetro, caudal y longitud."
            except Exception as e:
                return "Error en cálculo."

        elif "tirolina" in comando_lower or "tension" in comando_lower or "tensión" in comando_lower or self.modo_operativo == "tirolina":
            try:
                if "tirolina" in comando_lower and not any(char.isdigit() for char in comando_lower):
                    self.modo_operativo = "tirolina"
                    return "Módulo de tirolinas activado. Indica carga, claro y flecha."

                match_carga = re.search(r'(?:carga|peso)\s*[:=]?\s*(\d+\.?\d*)', comando_lower)
                match_claro = re.search(r'(?:claro|distancia|longitud)\s*[:=]?\s*(\d+\.?\d*)', comando_lower)
                match_flecha = re.search(r'flecha\s*[:=]?\s*(\d+\.?\d*)', comando_lower)

                numeros = [float(n) for n in re.findall(r'\d+\.?\d*', comando)]

                carga = float(match_carga.group(1)) if match_carga else (numeros[0] if len(numeros) > 0 else 0)
                claro = float(match_claro.group(1)) if match_claro else (numeros[1] if len(numeros) > 1 else 0)
                flecha = float(match_flecha.group(1)) if match_flecha else (numeros[2] if len(numeros) > 2 else 0)

                if flecha > 0 and carga > 0 and claro > 0:
                    tension = (claro * carga) / (4.0 * flecha)
                    resultado_str = f"Tensión de tirolina: {tension:.2f} kN."
                    self.ultimo_calculo = resultado_str
                    self.modo_operativo = None
                    return resultado_str
                else:
                    self.modo_operativo = "tirolina"
                    return "Indica carga, claro y flecha."
            except Exception as e:
                return "Error en cálculo."

        elif any(op in comando_lower for op in ["+", "-", "*", "/", "por", "entre", "cuánto es"]):
            try:
                expr = comando_lower.replace("cuánto es", "").replace("calcula", "").strip()
                expr = expr.replace("por", "*").replace("entre", "/").replace("x", "*")
                expr_limpia = re.sub(r'[^0-9\+\-\*\/\.\(\)]', '', expr)
                
                if expr_limpia:
                    resultado = eval(expr_limpia)
                    resultado_str = f"{resultado}"
                    self.ultimo_calculo = resultado_str
                    return resultado_str
            except Exception:
                pass

        elif "abre" in comando_lower or "ejecuta" in comando_lower or "abrir" in comando_lower:
            limpio = comando_lower.replace("jarvis", "").replace("por favor", "").strip()
            app_nombre = limpio.replace("abre", "").replace("ejecuta", "").replace("abrir", "").strip()
            return self.ejecutar_accion_app(app_nombre)

        else:
            self.memoria.guardar_dato(f"consulta_{datetime.datetime.now().strftime('%H%M%S')}", comando)
            return "Instrucción registrada. ¿Qué deseas hacer a continuación?"

    def obtener_estado_bateria(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                IntentFilter = autoclass('android.content.IntentFilter')
                Intent = autoclass('android.content.Intent')
                
                context = PythonActivity.mActivity
                filter_obj = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
                battery_status = context.registerReceiver(None, filter_obj)
                
                level = battery_status.getIntExtra('level', -1)
                scale = battery_status.getIntExtra('scale', -1)
                battery_pct = int((level / float(scale)) * 100) if scale > 0 else 0
                
                return f"Nivel de batería al {battery_pct} por ciento."
            except Exception as e:
                return f"No se pudo consultar la batería: {str(e)}"
        else:
            return "Sistemas al 100 por ciento (Simulación de PC)."

    def controlar_linterna(self, accion):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Context = autoclass('android.content.Context')
                
                context = PythonActivity.mActivity
                camera_manager = context.getSystemService(Context.CAMERA_SERVICE)
                camera_list = camera_manager.getCameraIdList()
                
                if camera_list.length > 0:
                    camera_id = camera_list[0]
                    encender = True if accion == "enciende" else False
                    camera_manager.setTorchMode(camera_id, encender)
                    self.linterna_encendida = encender
                    estado_str = "encendida" if encender else "apagada"
                    return f"Linterna {estado_str}."
                else:
                    return "No se detectó flash en la cámara."
            except Exception as e:
                return f"Error al controlar linterna: {str(e)}"
        else:
            return f"Linterna {accion}da (Simulación de PC)."

    def ejecutar_llamada(self, destino):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                
                context = PythonActivity.mActivity
                uri = Uri.parse(f"tel:{destino}")
                intent = Intent(Intent.ACTION_DIAL, uri)
                
                context.startActivity(intent)
                return f"Llamando a {destino}."
            except Exception as e:
                return f"Error al realizar la llamada: {str(e)}"
        else:
            return f"Llamando a '{destino}' (Simulación de PC)."

    def ejecutar_accion_app(self, nombre_app):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                PackageManager = autoclass('android.content.pm.PackageManager')
                
                context = PythonActivity.mActivity
                package_manager = context.getPackageManager()
                
                if "whatsapp" in nombre_app.lower():
                    intent = package_manager.getLaunchIntentForPackage("com.whatsapp")
                elif "ajustes" in nombre_app.lower() or "configuración" in nombre_app.lower():
                    intent = Intent(autoclass('android.provider.Settings').ACTION_SETTINGS)
                else:
                    return f"Sí, señor. No tengo registrada la aplicación {nombre_app}."
                
                if intent:
                    context.startActivity(intent)
                    return f"Sí, señor. {nombre_app} abierto."
                else:
                    return f"Sí, señor. Aplicación no disponible."
            except Exception as e:
                return f"Sí, señor. Error: {str(e)}"
        else:
            return f"Sí, señor. Abriendo '{nombre_app}' (Simulación de PC)."

class JarvisApp(App):
    def build(self):
        self.title = "J.A.R.V.I.S. Core - Táctico Autónomo"
        return JarvisInterface()

if __name__ == '__main__':
    JarvisApp().run()