import pandas as pd
from datetime import datetime

from vikur import Vikur

def highlight_cells(M, x):

  # Litir í stundatöflu
  colors = ['#CC99FF','#660066','#33CCCC','#FFFFCC','#99CCFF','#FF6600',
            '#003366','#99CC00','#003300','#808080','#FFCC99','#FFFF99',
            '#0000FF','#0066CC','#9999FF','#969696','#CCFFFF','#00CCFF',
            '#FFFF00','#00FF00','#00FFFF','#C0C0C0','#008080','#808000',
            '#666699','#800080','#993366','#800000','#333333','#FF9900',
            '#CCFFCC','#FF0000','#000080','#333300','#FF99CC','#FFCC00',
            '#339966','#FF00FF','#CCCCFF','#3366FF','#993300','#FF8080',
            '#333399','#008000']

  color_table = dict()
  for i, namskeid in enumerate(sorted(list(set(M.klinik).union(M.val_listi)))):
    color_table.update({ namskeid: colors[i % len(colors)] })

  df = x.copy()
  df.loc[:,:] = ''
  for nemandi in x.index:
    for v in x.columns:
      t = x.loc[nemandi, v]
      if isinstance(t, str):
        if t in color_table:
          if t in M.klinik_vikur:
            for w in M.klinik_vikur[t][v]:
              df.loc[nemandi,w] = f'background-color: {color_table[t]}'
          else:
            for w in M.val_vikur[t]:
              df.loc[nemandi,w] = f'background-color: {color_table[t]}'
  return df

# Ár frá viku
def arv(a, v, mid):
  if v < mid:
    return a+1
  return a

# Dagsetning frá ári og viku, mánudagur
def dags_upphaf(a, v, mid):
  return datetime.strptime(f'{arv(a, v, mid)}-{v}-1', '%Y-%W-%w').strftime('%d/%m/%Y')

# Dagsetning frá ári og viku, sunnudagur
def dags_lok(a, v, mid):
  return datetime.strptime(f'{arv(a, v, mid)}-{v}-0', '%Y-%W-%w').strftime('%d/%m/%Y')

def generate_excel(M, x, year, out_dir):
  V = Vikur()

  # MRS-leg skjöl

  mid = 25

  for c in M.klinik:
    df = pd.DataFrame(columns=['Fullt nafn nema', 'Kennitala', 'Kyn', 'Netfang',
                              'Farsími', 'Þjóðerni (ISO kóði)', 'Starfsheiti (kóði)',
                              'Kennitala leiðbeinanda', 'Deild (viðfang)', 'Frá',
                              'Til', 'Dagar/viku', 'Athugasemd',
                              'Námstig (GYMNASIUM, GRADUATE, POSTGRADUATE',
                              'Skóli (kóði/nafn)',
                              'Námsgráða (ef postgrad) (ss. CP, Diploma, MD, MPH, EDS',
                              'Aðalnámsgrein (kóði/nafn)', 'Sérnámsgrein (kóði/nafn)',
                              'Land erlends skóla (ISO kóði)', 'Samtök (kóði/nafn)',
                              'Áætluð útskrift', 'Nemandi hefur undirritað þagnarheiti',
                              'Nemandi hefur undirritað reglur um notkun sjúkraskrárupplýsinga',
                              'Auðkenniskort hefur verið afgreitt',
                              'Nemandi þarf tölvuaðgang',
                              'Nemandi hefur farið í heilbrigðisviðtal',
                              'Nemandi þarf mynd í auðkenniskort',
                              'Nemandi þarf auðkenniskort',
                              'Nemandi sækir auðkenniskort til skrifstofu',
                              'Nemandi sækir auðkenniskort til umsjónarmanns',
                              'Ónotað', 'Deild', 'Deildarstjóri',
                              'Netfang (deild)', 'Símanúmer'])
    i = 1
    for w in sorted(V.raun.keys()):
      v = V.raun[w]
      if v in M.klinik[c] and len(M.klinik[c][v]) > 0:
        df.loc[i] = { 'Fullt nafn nema': f'Vika {v}' }
        i += 1
        for d in M.klinik[c][v]:
          skradir = 0
          for s in M.nemendur:
            if x[s,c,v,d].X > 0:
              upphafsvika = min(M.klinik_vikur[c][v])
              lokavika = max(M.klinik_vikur[c][v])
              skradir += 1
              df.loc[i] = { 'Fullt nafn nema': M.nemendur[s].nafn.title(),
                          'Kennitala': M.nemendur[s].kennitala,
                          'Netfang': M.nemendur[s].netfang,
                          'Farsími': M.nemendur[s].farsimi,
                          'Deild (viðfang)': M.klinik[c][v][d].vidfang,
                          'Frá': dags_upphaf(year, upphafsvika, mid),
                          'Til': dags_lok(year, lokavika, mid),
                          'Deild': M.klinik[c][v][d].heiti,
                          'Deildarstjóri': M.klinik[c][v][d].stjori.title(),
                          'Netfang (deild)': M.klinik[c][v][d].netfang,
                          'Símanúmer': M.klinik[c][v][d].simanumer }
              i += 1
          while skradir < M.klinik[c][v][d].plass:
            skradir += 1
            df.loc[i] = { 'Fullt nafn nema': '',
                          'Kennitala': '',
                          'Netfang': '',
                          'Farsími': '',
                          'Deild (viðfang)': M.klinik[c][v][d].vidfang,
                          'Frá': dags_upphaf(year, upphafsvika, mid),
                          'Til': dags_lok(year, lokavika, mid),
                          'Deild': M.klinik[c][v][d].heiti,
                          'Deildarstjóri': M.klinik[c][v][d].stjori.title(),
                          'Netfang (deild)': M.klinik[c][v][d].netfang,
                          'Símanúmer': M.klinik[c][v][d].simanumer }
            i += 1
    df.to_excel(f'{out_dir}/mrs_radad_{c}.xlsx')

  # Allar skráningar
  # Reikna síðustu viku í klíník fyrir hvern nemanda
  sidasta_vika = dict()
  sidasta_vika_serstakt = { s: dict() for s in M.nemendur }

  # Normaliserar vikur; raðar þeim frá 0 eftir röð innan skólaárs
  allar_vikur = M.vikur.copy()
  for c in M.klinik_vikur:
    for w in M.klinik_vikur[c]:
      allar_vikur = allar_vikur | M.klinik_vikur[c][w]
  for c in M.val_vikur:
    allar_vikur = allar_vikur | set(M.val_vikur[c])

  vikur_fyrir = { v for v in allar_vikur if v > mid }
  vikur_eftir = { v for v in allar_vikur if v < mid }
  vikur_radadar = [v for v in vikur_fyrir] + [v for v in vikur_eftir]

  nemindex = ['Dagsetning'] + list(M.nemendur.keys())
  nemcols = ['Nafn'] + vikur_radadar

  stundatafla = pd.DataFrame('', index=nemindex, columns=nemcols)

  for col in stundatafla.columns:
    if col == 'Nafn':
      stundatafla[col] = [''] + [M.nemendur[s].nafn for s in stundatafla.index if s != 'Dagsetning']
    else:
      stundatafla[col]['Dagsetning'] = dags_upphaf(year, col, mid)

  # Valnámskeið
  for s in M.nemendur:
    for c in M.val_nemenda[s]:
      if M.val_nemenda[s][c] > 0:
        for v in M.val_vikur[c]:
          stundatafla.loc[s,v] = f'{c}'

  # Klínísk námskeið
  for s in M.nemendur:
    for c in M.klinik:
      for v in M.klinik[c]:
        if v > 0:
          for d in M.klinik[c][v]:
            if x[s,c,v,d].X > 0:
              # Þurfum víst ekki deild
              # stundatafla.loc[s,v] = f'{c} ({d})'
              stundatafla.loc[s,v] = f'{c}'
              if s not in sidasta_vika:
                sidasta_vika[s] = v
              else:
                if V.sym[v] > V.sym[sidasta_vika[s]]:
                  sidasta_vika[s] = v
              sidasta_vika_serstakt[s][c] = v

  for s in M.nemendur:
    if s not in sidasta_vika:
      sidasta_vika[s] = 0

  stundatafla_lit = stundatafla.style.apply(lambda x: highlight_cells(M, x), axis=None)
  stundatafla_lit.to_excel(f'{out_dir}/stundatafla.xlsx')

  # Skráningar
  skraningar = pd.DataFrame(index=M.klinik, columns=vikur_radadar)

  for s in M.nemendur:
    for c in M.klinik:
      for v in M.klinik[c]:
        if v >= 0:
          for d in M.klinik[c][v]:
            if x[s,c,v,d].X > 0:
              if pd.isna(skraningar.loc[c,v]):
                skraningar.loc[c,v] = 1
              else:
                skraningar.loc[c,v] += 1

  for v in skraningar.columns:
    for c in skraningar.index:
      if v >= 0 and not pd.isna(skraningar.loc[c,v]):
        skraningar.loc[c,v] = f'{skraningar.loc[c,v]} / {sum(M.klinik[c][v][d].plass for d in M.klinik[c][v])}'

  skraningar.to_excel(f'{out_dir}/skraningar.xlsx')