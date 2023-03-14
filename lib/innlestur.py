import os
from model_data import ModelData
from deild import Deild
from nemandi import Nemandi
from clean import read_clean_excel, clean_split
from advorun import wprint

def lesa_namskeid(filename):
  df = read_clean_excel(filename)
  vikur = dict()
  for row in df.iterrows():
    row = row[1]
    if row['vika'] not in vikur:
      vikur[row['vika']] = dict()
    postnumer = [101]
    if not row['póstnúmer'] == '':
      postnumer = [int(i) for i in clean_split(row['póstnúmer'], ';')]
    stadsetning = 'höfuðborgarsvæðið'
    if row['höfuðborgarsvæði'] == 0:
      stadsetning = row['staður']
    vikur[row['vika']][row['deild']] = Deild(row['deild'], str(row['viðfang']).rjust(5, '0'), row['pláss'], stadsetning, postnumer, row['deildarstjóri'], row['netfang'], row['símanúmer'])
  return { df['námskeið'][0]: vikur }

def lesa_gogn(in_dir, generate_extra_weeks = True):
  print('-'*40)
  print('Hef innlestur...')

  M = ModelData()

  stundatafla_df = read_clean_excel(f'{in_dir}/stundatafla.xlsx')

  vikur = set()
  for vika in stundatafla_df['vika']:
    vikur.add(vika)
  M.vikur = vikur

  #----------------------------------------------------------------------------
  # MRS skjöl

  namskeid = dict()
  try:
    for filename in os.listdir(in_dir):
      if filename.startswith('mrs_stadlad_'):
        namskeid.update(lesa_namskeid(f'{in_dir}/{filename}'))

    for c in namskeid:
      for vika in vikur:
        if vika not in namskeid[c]:
          namskeid[c][vika] = dict()

  except:
    wprint('Klíník ekki lesin inn')

  M.klinik = namskeid
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Nemendur
  nemendur_df = read_clean_excel(f'{in_dir}/nemendur.xlsx')

  nemendur = dict()
  try:
    for i, nemandi in enumerate(nemendur_df['notandanafn']):
      nemendur[nemandi] = Nemandi(nemendur_df['nafn'][i], str(nemendur_df['kennitala'][i]).rjust(10, '0'), nemendur_df['notandanafn'][i], nemendur_df['farsími'][i], nemendur_df['póstnúmer'][i], 0)
      if nemendur[nemandi].postnumer == '':
        nemendur[nemandi].postnumer = 101

  except:
    wprint('Listi af nemendum ekki búinn til')

  M.nemendur = nemendur
  #----------------------------------------------------------------------------
  # Skráning nemenda

  nemendaskraning = dict()
  try:
    for i, nemandi in enumerate(nemendur_df['notandanafn']):
      nemendaskraning[nemandi] = dict()
      for nam in namskeid:
        if len(str(nemendur_df[nam.lower()][i])) > 0:
          nemendaskraning[nemandi][nam] = 1
        else:
          nemendaskraning[nemandi][nam] = 0

  except:
    wprint('Engin skráning í klíník')

  M.nemendaskraning = nemendaskraning

  val_vikur = dict()
  val_listi = set()
  try:
    # dict fyrir vikur valnámskeiða
    val_listi = set(stundatafla_df[stundatafla_df['klíník í viku'] == '']['námskeið'])

    for val in val_listi:
      val_vikur.update({
        val: stundatafla_df[stundatafla_df['námskeið'] == val]['vika'].tolist()
      })

  except:
    wprint('Völ ekki lesin inn')

  M.val_listi = val_listi
  M.val_vikur = val_vikur

  val_nemenda = dict()
  try:
    for i, nemandi in enumerate(nemendur_df['notandanafn']):
      val_nemenda[nemandi] = dict()
      for val in val_vikur:
        if len(str(nemendur_df[val.lower()][i])) > 0:
          val_nemenda[nemandi][val] = 1
        else:
          val_nemenda[nemandi][val] = 0

  except:
    wprint('Engin skráning í val')

  M.val_nemenda = val_nemenda
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Skrá nemendur á sama stað
  sami_stadur_df = read_clean_excel(f'{in_dir}/sami_stadur.xlsx')

  sami_stadur = dict()
  try:
    for s in nemendur:
      sami_stadur[s] = { c: set() for c in namskeid }
    for i, netfang in enumerate(sami_stadur_df['netfang']):
      sami_stadur[netfang][sami_stadur_df['námskeið'][i]] = set(clean_split(sami_stadur_df['staður'][i], ';'))

  except:
    wprint('Engin skráning á tiltekinn stað')

  M.sami_stadur = sami_stadur
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Skrá nemendur á annan stað
  ekki_sami_stadur_df = read_clean_excel(f'{in_dir}/ekki_sami_stadur.xlsx')

  ekki_sami_stadur = dict()
  try:
    for s in nemendur:
      ekki_sami_stadur[s] = { c: set() for c in namskeid }
    for i, netfang in enumerate(ekki_sami_stadur_df['netfang']):
      ekki_sami_stadur[netfang][ekki_sami_stadur_df['námskeið'][i]] = set(clean_split(ekki_sami_stadur_df['staður'][i], ';'))

  except:
    wprint('Engin skráning utan tiltekins staðar')

  M.ekki_sami_stadur = ekki_sami_stadur

  #----------------------------------------------------------------------------
  # Námskeið sem taka margar vikur
  stundatafla_klinik = stundatafla_df[stundatafla_df['klíník í viku'] != '']
  stundatafla_klinik = stundatafla_klinik.astype({ 'klíník í viku': int })
  kmv = stundatafla_klinik[stundatafla_klinik['vikur']>1]

  klinik_margar_vikur = dict()
  try:
    for c in set(kmv['námskeið']):
      temp = dict()
      for i in kmv[kmv['námskeið'] == c].index:
        x = list(range(1, kmv.loc[i, 'vikur']+1))
        q = kmv.loc[i, 'klíník í viku']
        x.remove(q)
        v = kmv.loc[i, 'vika']
        y = [v + k - 1 for k in x]
        temp.update({ v + q - 1: y })
      klinik_margar_vikur.update({ c: temp })

  except:
    wprint('Engin klíník í margar vikur')

  M.klinik_margar_vikur = klinik_margar_vikur
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Vikur per hólf
  klinik_vikur = dict()
  for c in set(stundatafla_klinik['námskeið']):
    temp = dict()
    for i in stundatafla_klinik[stundatafla_klinik['námskeið'] == c].index:
      v = stundatafla_klinik.loc[i, 'vika']
      q = stundatafla_klinik.loc[i, 'klíník í viku']
      n = stundatafla_klinik.loc[i, 'vikur']
      temp.update({ v + q - 1: set(range(v, v + n)) })
    klinik_vikur.update({ c: temp })

  M.klinik_vikur = klinik_vikur
  #----------------------------------------------------------------------------
  # Nemendur sem þurfa að klára alla klíník snemma
  klara_snemma = dict()
  try:
    klara_snemma_df = read_clean_excel(f'{in_dir}/klara_snemma.xlsx')

    for i, netfang in enumerate(klara_snemma_df['netfang']):
      klara_snemma[netfang] = klara_snemma_df['vika'][i]

    for nem in M.nemendur:
      if nem in klara_snemma:
        M.nemendur[nem].olett = 1

  except:
    wprint('Enginn klárar allt snemma')

  M.klara_snemma = klara_snemma
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Nemendur sem þurfa að klára tiltekna klíník snemma
  klara_snemma_serstakt = dict()
  try:
    klara_snemma_serstakt_df = read_clean_excel(f'{in_dir}/klara_snemma_serstakt.xlsx')

    for s in nemendur:
      klara_snemma_serstakt[s] = dict()

    for i, netfang in enumerate(klara_snemma_serstakt_df['netfang']):
      klara_snemma_serstakt[netfang][klara_snemma_serstakt_df['námskeið'][i]] = klara_snemma_serstakt_df['vika'][i]

  except:
    wprint('Enginn klárar sérstaka klíník snemma')

  M.klara_snemma_serstakt = klara_snemma_serstakt
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Skrá nemendur á sömu deild
  sama_deild = dict()
  try:
    sama_deild_df = read_clean_excel(f'{in_dir}/sama_deild.xlsx')

    for s in nemendur:
      sama_deild[s] = { c: set() for c in namskeid }
    for i, netfang in enumerate(sama_deild_df['netfang']):
      nam = sama_deild_df['námskeið'][i]
      for deild in clean_split(sama_deild_df['deild'][i], ';'):
        if netfang in nemendur:
          sama_deild[netfang][nam].add(deild)

  except:
    wprint('Engin skráning á tiltekna deild')

  M.sama_deild = sama_deild
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Skrá nemendur á aðra deild
  ekki_sama_deild = dict()
  try:
    ekki_sama_deild_df = read_clean_excel(f'{in_dir}/ekki_sama_deild.xlsx')

    for s in nemendur:
      ekki_sama_deild[s] = { c: set() for c in namskeid }
    for i, netfang in enumerate(ekki_sama_deild_df['netfang']):
      nam = ekki_sama_deild_df['námskeið'][i]
      for deild in clean_split(ekki_sama_deild_df['deild'][i], ';'):
        ekki_sama_deild[netfang][nam].add(deild)

  except:
    wprint('Engin skráning utan tiltekinnar deildar')

  M.ekki_sama_deild = ekki_sama_deild
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Laga heiti.....
  try:
    import pandas as pd
    rangar_deildir = read_clean_excel('excel/rangar_deildir.xlsx')

    deild_dict = dict()
    for d in rangar_deildir.iterrows():
      if not pd.isna(d[1][1]):
        deild_dict[d[1][0]] = d[1][1]
      else:
        deild_dict[d[1][0]] = d[1][0]

    # Laga deildanöfn
    for s in M.sama_deild:
      for c in M.sama_deild[s]:
        M.sama_deild[s][c] = { deild_dict[d] if d in deild_dict else d for d in M.sama_deild[s][c] }
    for s in M.ekki_sama_deild:
      for c in M.ekki_sama_deild[s]:
        M.ekki_sama_deild[s][c] = { deild_dict[d] if d in deild_dict else d for d in M.ekki_sama_deild[s][c] }

  except:
    wprint('Engar deildir til að leiðrétta')
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Óskir um frívikur
  fri_osk = dict()
  try:
    fri_osk_df = read_clean_excel(f'{in_dir}/fri_osk.xlsx')

    for i, netfang in enumerate (fri_osk_df['netfang']):
      fri_osk[netfang] = set(clean_split(fri_osk_df['vikur'][i], ';'))

  except:
    wprint('Engin ósk um frí')

  M.fri_osk = fri_osk
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Skilyrtar frívikur
  fri_skilyrt = dict()
  try:
    fri_skilyrt_df = read_clean_excel(f'{in_dir}/fri_skilyrt.xlsx')

    for i, netfang in enumerate (fri_skilyrt_df['netfang']):
      fri_skilyrt[netfang] = set(clean_split(fri_skilyrt_df['vikur'][i], ';'))

  except:
    wprint('Ekkert skilyrt frí')

  M.fri_skilyrt = fri_skilyrt
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # vikur sem nemendur eru í valnámskeiðum
  nemendur_val_vikur = dict()

  for s in M.val_nemenda:
    tmp = set()
    for c in M.val_nemenda[s]:
      if M.val_nemenda[s][c] > 0:
        tmp.update(set(M.val_vikur[c]))
    nemendur_val_vikur.update({ s: tmp })

  M.nemendur_val_vikur = nemendur_val_vikur
  #----------------------------------------------------------------------------

  M.generate_extra_data()
  if generate_extra_weeks:
    M.generate_extra_weeks()

  print('Innlestri lokið')
  print('-'*40)

  return M