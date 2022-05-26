import os
import requests

from .models import Consumidor, Gasto

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

##########
# FORMAT #
##########

def getCurrencyHtml(number):
    n = '{:,.2f} €'.format(number) 
    if number >= 0:
        ret = f'<span style="color:green;">{n}</span>'
    else:
        ret = f'<span style="color:red;">{n}</span>'
    return ret


########
# MAIL #
########

def send_mailgun_mail(to_list, subject_str, text_str, files_list ):
    # Carregem el fitxer pcr.env
    lines = [line.rstrip('\n') for line in open(os.path.join(BASE_DIR, 'pcr.env'))]
    # convertim el .env en un diccionari clau valor amb: url, api, from
    env = {}
    for line in lines:
        key_value = line.split("=")
        env[key_value[0]] = key_value[1]

    res = requests.post(
        env['url'], # "http://localhost/phphttpmail/index.php",
        auth=("api", env["api"]),
        files=files_list,
        data={"from": env["from"],
              "to": to_list,
              "subject": subject_str,
              "text": text_str})

    print("REQUEST ----> ", res.text)


#######
# CSV #
#######

def import_csv_consumidor(file):
    print(file)
    text_file_unix_to_windows(file, 7)
    f = open(file)
    lines = f.read().split('\r\n')
    # lines = [line.rstrip('\r\n') for line in open(file)]
    for line in lines:
        row = line.split(';')
        print("[ ROW ]", row)
        _, created = Consumidor.objects.get_or_create(
            # El id és el row[0] i és autoincrement
            nombre = row[1],
            telefono = row[2],
            direccion = row[3],
            email = row[4]
            # row[5] - row[6] = created, updated
        )


def import_csv_pedido(file):
    print(file)
    text_file_unix_to_windows(file, 25)
    f = open(file)
    lines = f.read().split('\r\n')
    # lines = [line.rstrip('\r\n') for line in open(file)]
    for line in lines:
        row = line.split(';')
        print("[ ROW ]", row)
        _, created = Gasto.objects.get_or_create(
            # El id és el row[0] i és autoincrement
            consumidor = row[1],
            dia = row[2],
            dia_evento = row[3],
            dia_pedido = row[4],
            dia_entrega = row[5],
            lugar_evento = row[6],
            nos_conocio = row[7]
        )


def import_csv_gasto(file, ejercicio, mes):
    #print(file)
    #text_file_unix_to_windows(file, 10)
    f = open(file)
    lines = f.readlines()
    #lines = f.read().split('\n') # '\r\n'
    # lines = [line.rstrip('\r\n') for line in open(file)]
    for line in lines:
        row = line.split(';')
        #print("[ ROW ]", mes, f"conta: {row[0]}", f"nom: {row[1]}", f"debe: {row[4]}", f"haber: {row[5]}")
        gasto, created = Gasto.objects.get_or_create(
            # El id és el row[0] i és autoincrement
            ejercicio = ejercicio,
            cuenta = row[0],
            nombre = row[1],
        )
        debe = float(row[4].replace(".", "").replace(",","."))
        haber = float(row[5].replace(".", "").replace(",","."))
        setattr(gasto, mes, (debe - haber) * -1)
        gasto.save()


def text_file_unix_to_windows(file, total_cols):
    ''' 
        Passem el fitxer de text a format windows \r\n. Això ens permet
        a les funcions anteriors poder tenir \n en un camp textfield multi
        línia com pot ser la direcció.
    '''
    f = open(file, 'r')
    # Array de columnes, no tenim en compte les línies
    cols = f.read().split(';')
    # Muntem les línies segons el total_cols
    new_lines = ""
    line = ""
    col_count = 1
    for col in cols:
        col_count += 1
        # Si ja tenim una línia muntada
        if col_count > total_cols:
            # Netejem retorns de carro, unix o win
            coln = ""
            col1 = ""
            #print("- COLS: ", col)
            if '\r\n' in col: # line[-2:] == 
                coln, col1 = col.split('\r\n')
                line += coln
            elif '\n' in col:
                coln, col1 = col.split('\n')
                line += coln
            # La nova línia té format windows
            new_lines += line + '\r\n'
            #print("[ " + line + " ]")
            col_count = 2
            line = col1 + ";"
        else:
            line += col
            line += ';'
    f.close()
    # Sobreescrivim el fitxer amb format windows.
    f = open(file, 'w')
    f.write(new_lines)



########################
# HANDLE UPLOADED FILE #
########################

def handle_uploaded_file(f):
    """
        Per capturar el fitxer CSV pujat per un formulari desde la vista que
        el rep i guardar-lo al directòri static/csv/.
    """
    abs_file_name = os.path.join(BASE_DIR, 'static/csv/' + f.name)
    with open(abs_file_name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return abs_file_name