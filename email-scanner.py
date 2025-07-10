import pyfiglet
import subprocess
import requests
import shutil
from bs4 import BeautifulSoup
from colorama import init, Fore

init(autoreset=True)

def imprimir_banner():
    raw_banner = pyfiglet.figlet_format("EMAIL OSINT", font="slant").splitlines()

    # Degradado de color: rojo → amarillo → verde → cian → azul → magenta
    colores = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    
    print(Fore.WHITE + "=" * 70)
    for i, linea in enumerate(raw_banner):
        color = colores[i % len(colores)]
        print(color + linea)
    print(Fore.WHITE + "=" * 70)
    print(Fore.GREEN + "🔍 Herramienta OSINT de búsqueda de correos electrónicos")
    print(Fore.GREEN + "👤 by: zm1c\n")

def buscar_con_holehe(email):
    print(Fore.BLUE + f"\nBuscando información del correo {email} usando holehe...\n")
    
    path_holehe = shutil.which('holehe')

    if not path_holehe:
        print(Fore.RED + "❌ Error: no se encontró la herramienta 'holehe'. Asegúrate de tenerla instalada y que esté en el PATH.")
        print(Fore.YELLOW + "👉 Prueba exportar tu PATH así: export PATH=$HOME/.local/bin:$PATH")
        return
    
    try:
        resultado = subprocess.run(
            [path_holehe, '--only-used', email],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if resultado.returncode == 0:
            salida = resultado.stdout.strip()
            salida_filtrada = '\n'.join([linea for linea in salida.splitlines() if '[+]' in linea])

            if salida_filtrada:
                print(Fore.BLUE + "[+] Resultados encontrados con holehe:")
                print(Fore.CYAN + salida_filtrada)
            else:
                print(Fore.RED + "\nNo se encontraron sitios asociados a este correo.")
        else:
            print(Fore.RED + f"\nError al ejecutar holehe:\n{resultado.stderr}")
    except Exception as e:
        print(Fore.RED + f"❌ Error inesperado al ejecutar holehe: {e}")

def obtener_datos_mailru(email):
    usuario = email.split('@')[0]
    url = f"https://my.mail.ru/mail/{usuario}/"
    mensaje_resultado = [f"Enlace al perfil de Mail.ru: {url}"]
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        respuesta = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as e:
        return f"❌ Error al conectarse a Mail.ru: {e}"

    if respuesta.status_code == 200:
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        
        avatar = soup.find('img', {'class': 'profile-avatar__img'})
        if avatar and 'src' in avatar.attrs:
            mensaje_resultado.append(f"Avatar: {avatar['src']}")
        
        nombre = soup.find('h1', {'itemprop': 'name'})
        if nombre:
            mensaje_resultado.append(f"Nombre completo: {nombre.get_text(strip=True)}")
        
        ciudad_tag = soup.find('li', {'class': 'b-right-column__block__anketa__item--city'})
        if ciudad_tag:
            ciudad = ciudad_tag.find('div', {'class': 'b-right-column__block__anketa__item__body__text'})
            if ciudad:
                mensaje_resultado.append(f"Ubicación: {ciudad.get_text(strip=True)}")
        
        nacimiento = soup.find('span', {'class': 'b-right-column__block__anketa__item__body__text', 'itemprop': 'birthDate'})
        if nacimiento:
            mensaje_resultado.append(f"Fecha de nacimiento: {nacimiento.get_text(strip=True)}")
        
        descripcion = soup.find('div', {'class': 'about-info__description'})
        if descripcion:
            mensaje_resultado.append(f"Sobre mí: {descripcion.get_text(strip=True)}")
        
        return '\n'.join(mensaje_resultado)
    else:
        return "No se pudo acceder al perfil de Mail.ru."

def revisar_fugas(email):
    url = f"https://leakcheck.net/api/public?check={email}"
    try:
        respuesta = requests.get(url, timeout=10)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            if datos.get('success') and datos.get('found', 0) > 0:
                fuga_info = "\n[+] Se encontraron filtraciones para este correo:"
                for fuente in datos.get('sources', []):
                    if 'name' in fuente and 'date' in fuente:
                        fuga_info += f"\n- Fuente: {fuente['name']}, Fecha: {fuente['date']}"
                return fuga_info
            else:
                return "No se encontraron filtraciones para este correo."
        else:
            return f"Error al conectar con LeakCheck: Código {respuesta.status_code}"
    except requests.RequestException as e:
        return f"❌ Error en la solicitud: {e}"

def buscar_en_hudsonrock(email):
    print(Fore.BLUE + f"\nBuscando información de {email} en HudsonRock...\n")
    
    try:
        url = f"https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-email?email={email}"
        respuesta = requests.get(url, timeout=10)
        
        if respuesta.status_code == 200:
            try:
                datos = respuesta.json()
                
                if datos and 'stealers' in datos:
                    robos = datos['stealers']
                    if not robos:
                        print(Fore.RED + "\nNo se encontró información comprometida.")
                        return

                    print(Fore.BLUE + "\n[HudsonRock] Información encontrada:")
                    for robo in robos:
                        print(Fore.CYAN + f"\n> Servicios corporativos: {robo['total_corporate_services']}")
                        print(Fore.CYAN + f"> Servicios de usuario: {robo['total_user_services']}")
                        print(Fore.CYAN + f"> Fecha de compromiso: {robo['date_compromised']}")
                        print(Fore.CYAN + f"> Nombre del equipo: {robo['computer_name']}")
                        print(Fore.CYAN + f"> Sistema operativo: {robo['operating_system']}")
                        print(Fore.CYAN + f"> Dirección IP: {robo['ip']}")
                        print(Fore.CYAN + f"> Contraseñas comunes: {', '.join(robo['top_passwords'])}")
                        print(Fore.CYAN + f"> Usuarios frecuentes: {', '.join(robo['top_logins'])}")
                        print(Fore.GREEN + "\n------------------------------------------------------\n")
                else:
                    print(Fore.RED + "\nNo se encontró información comprometida.")
            except ValueError as e:
                print(Fore.RED + f"\nError al interpretar la respuesta JSON: {e}")
        else:
            print(Fore.RED + f"\nError en la solicitud: Código {respuesta.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"❌ Error de conexión: {e}")

def mostrar_resultados():
    print(Fore.BLUE + "\n=============================================")
    input(Fore.CYAN + "\nPresiona Enter para volver al menú principal.")
    print(Fore.BLUE + "=============================================")

def main():
    imprimir_banner()

    while True:
        email = input(Fore.CYAN + "Ingresa un correo electrónico: ").strip()

        # Validar dominios permitidos
        if not (email.endswith(".pe") or email.endswith(".com") or email.endswith("@mail.ru")):
            print(Fore.RED + "❌ Solo se permiten correos que terminen en '.pe', '.com' o '@mail.ru'")
            continue

        buscar_con_holehe(email)
        
        if '@mail.ru' in email:
            perfil = obtener_datos_mailru(email)
            if perfil:
                print(Fore.BLUE + "\n[+] Perfil encontrado en Mail.ru:")
                print(Fore.CYAN + perfil)
            else:
                print(Fore.RED + "\nNo se encontró perfil en Mail.ru.")

        resultado_fugas = revisar_fugas(email)
        print(Fore.BLUE + "\n[+] Resultado de filtraciones (LeakCheck):")
        print(Fore.CYAN + resultado_fugas)

        buscar_en_hudsonrock(email)

        mostrar_resultados()

        salir = input(Fore.RED + "¿Deseas salir del programa? (y/n): ").lower()
        if salir == 'y':
            print(Fore.RED + "Saliendo del programa.")
            break

if __name__ == '__main__':
    main()

