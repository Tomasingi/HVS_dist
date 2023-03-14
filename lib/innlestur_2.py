import pandas as pd
from model_data import ModelData
from deild import Deild
from nemandi import Nemandi
from clean_2 import read_clean_excel, clean_split

def lesa_namskeid(df, namskeid=None):
  vikur = dict()
  for row in df.iterrows():
    row = row[1]
    try:
      if row['vika'] not in vikur:
        vikur[row['vika']] = dict()

      postnumer = [101]
      if not row['póstnúmer'] == '':
        postnumer = [int(float(i)) for i in clean_split(row['póstnúmer'], ';')]

      hofudborgarsvaedi = True
      if row['höfuðborgarsvæði'] == 0 or row['höfuðborgarsvæði'] == '':
        hofudborgarsvaedi = False

      # Can be the empty string
      stadsetning = row['staður']

      vidfang = row['viðfang']
      if row['viðfang'] == '':
        vidfang = '00000'
      else:
        vidfang = str(int(vidfang)).rjust(5, '0')

      plass = row['pláss']
      try:
        plass = int(plass)
      except ValueError:
        raise Exception(f'Pláss verður að vera heiltala, fann {plass} í mrs skjali.')
      vikur[row['vika']][row['deild']] = Deild(row['deild'], vidfang, plass, stadsetning, hofudborgarsvaedi, postnumer, row['deildarstjóri'], row['netfang'], row['símanúmer'])
    except KeyError as kerr:
      if namskeid is not None:
        raise Exception(f'Vantar dálkinn {kerr} í mrs skjali undir {namskeid}.')
      raise Exception(f'Vantar dálkinn {kerr} í mrs skjali.')
  return { df['námskeið'][0]: vikur }

def read_data(in_dir, skraningar='skraningar.xlsx', mrs='mrs_stadlad.xlsx', auka_upplysingar='auka_upplysingar.xlsx'):
  M = ModelData()
  warnings = []

  skraningar_dfs = read_clean_excel(f'{in_dir}/{skraningar}', None)
  try:
    nemendur_df = skraningar_dfs['nemendur']
    stundatafla_df = skraningar_dfs['stundatafla']
  except KeyError as kerr:
    raise Exception(f'Vantar blað {kerr} í {skraningar} skrána.')

  mrs_dfs = read_clean_excel(f'{in_dir}/{mrs}', None)

  auka_upplysingar_dfs = read_clean_excel(f'{in_dir}/{auka_upplysingar}', None)
  try:
    sami_stadur_df = auka_upplysingar_dfs['sami_stadur']
    ekki_sami_stadur_df = auka_upplysingar_dfs['ekki_sami_stadur']
    klara_snemma_df = auka_upplysingar_dfs['klara_snemma']
    klara_snemma_serstakt_df = auka_upplysingar_dfs['klara_snemma_serstakt']
    sama_deild_df = auka_upplysingar_dfs['sama_deild']
    ekki_sama_deild_df = auka_upplysingar_dfs['ekki_sama_deild']
    # rangar_deildir = auka_upplysingar_dfs['vitlaus_deildanofn']
    fri_osk_df = auka_upplysingar_dfs['fri_osk']
    fri_skilyrt_df = auka_upplysingar_dfs['fri_skilyrt']
    akvedin_rodun_df = auka_upplysingar_dfs['akvedin_rodun']
  except KeyError as kerr:
    raise Exception(f'Vantar blað {kerr} í {auka_upplysingar} skrána.')

  vikur = set()
  for vika in stundatafla_df['vika']:
    vikur.add(vika)
  M.vikur = vikur

  #----------------------------------------------------------------------------
  # MRS skjöl

  namskeid = dict()

  if isinstance(mrs_dfs, dict):
    for x in mrs_dfs:
      namskeid.update(lesa_namskeid(mrs_dfs[x], x))
  else:
    namskeid.update(lesa_namskeid(mrs_dfs))

  if len(namskeid) == 0:
    raise Exception(f'Engin námskeið lesin úr MRS skjali')

  for c in namskeid:
    for vika in vikur:
      if vika not in namskeid[c]:
        namskeid[c][vika] = dict()

  M.klinik = namskeid

  # Deildir í hverju námskeiði - notað til að passa að gögn séu rétt
  klinik_deildir = dict()
  for c in namskeid:
    klinik_deildir[c] = set()
    for vika in namskeid[c]:
      for deild in namskeid[c][vika]:
        klinik_deildir[c].add(deild)

  # Staðir fyrir hvert námskeið - notað til að passa að gögn séu rétt
  klinik_stadir = dict()
  for c in namskeid:
    klinik_stadir[c] = set()
    for vika in namskeid[c]:
      for deild in namskeid[c][vika]:
        klinik_stadir[c].add(namskeid[c][vika][deild].stadur)
  # print(klinik_stadir)
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Nemendur

  nemendur = dict()
  try:
    for i, nemandi in enumerate(nemendur_df['notandanafn']):
      nemendur[nemandi] = Nemandi(nemendur_df['nafn'][i], str(nemendur_df['kennitala'][i]).rjust(10, '0'), nemendur_df['notandanafn'][i], nemendur_df['farsími'][i], nemendur_df['póstnúmer'][i], 0)
      if nemendur[nemandi].postnumer == '':
        nemendur[nemandi].postnumer = 101

  except KeyError as kerr:
    raise Exception(f'Vantar dálkinn {kerr} í nemenda hlutann í skránni {skraningar}')

  M.nemendur = nemendur
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Skráning nemenda í námskeið

  nemendaskraning = dict()
  try:
    for i, nemandi in enumerate(nemendur_df['notandanafn']):
      nemendaskraning[nemandi] = dict()
      failed_namskeid = set()
      for nam in namskeid:
        if nam not in failed_namskeid:
          try:
            if len(str(nemendur_df[nam.lower()][i])) > 0:
              nemendaskraning[nemandi][nam] = 1
            else:
              nemendaskraning[nemandi][nam] = 0
          except KeyError as kerr:
            warnings.append(f'Vantar dálkinn {kerr} í nemenda hlutann í skránni {skraningar}. Allir nemendur skráðir í námskeiðið.')
            failed_namskeid.add(nam)

    for nemandi in nemendur:
      for nam in failed_namskeid:
        nemendaskraning[nemandi][nam] = 1

  except KeyError as kerr:
    raise Exception(f'Vantar dálkinn {kerr} í nemenda hlutann í skránni {skraningar}')

  M.nemendaskraning = nemendaskraning

  # og í valnámskeið
  val_vikur = dict()
  val_listi = set()
  try:
    # dict fyrir vikur valnámskeiða
    val_listi = set(stundatafla_df[stundatafla_df['klíník byrjar í viku'] == '']['námskeið'])

    for val in val_listi:
      val_vikur.update({
        val: stundatafla_df[stundatafla_df['námskeið'] == val]['vika'].tolist()
      })

  except KeyError as kerr:
    raise Exception(f'Vantar dálkinn {kerr} í stundatöflu hlutann í skránni {skraningar}')

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

  except KeyError as kerr:
    raise Exception(f'Vantar dálkinn {kerr} í nemanda hlutann í skránni {skraningar}')

  M.val_nemenda = val_nemenda
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Skrá nemendur á sama stað

  sami_stadur = dict()
  try:
    failed_stadir = { c: set() for c in namskeid }

    for s in M.nemendur:
      sami_stadur[s] = { c: set() for c in namskeid }
    for i, netfang in enumerate(sami_stadur_df['netfang']):

      nams = set(clean_split(sami_stadur_df['námskeið'][i], ';'))

      if netfang not in M.nemendur:
        raise Exception(f'Nemandinn {netfang} í sami_stadur í {auka_upplysingar} fannst ekki í nemendaskráningu í {skraningar} skjalinu.')
      for c in nams:
        if c not in M.klinik:
          raise Exception(f'Námskeiðið {c} úr sami_stadur í {auka_upplysingar} fannst ekki í {mrs} skjalinu.')

      if len(nams) == 0:
        nams = namskeid

      stadir = set(clean_split(sami_stadur_df['staður'][i], ';'))
      for c in nams:
        for st in stadir:
          if st not in klinik_stadir[c]:
            failed_stadir[c].add(st)
            warnings.append(f'Staðurinn {st} í sami_stadur í {auka_upplysingar} fannst ekki í {mrs} skjalinu fyrir námskeiðið {c}.')
        sami_stadur[netfang][c] = stadir

  except KeyError as kerr:
    raise Exception(f'Rangt netfang/námskeið gefið í {auka_upplysingar}/sami_stadur: {kerr}')

  M.sami_stadur = sami_stadur
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Skrá nemendur á annan stað

  ekki_sami_stadur = dict()
  try:
    failed_stadir = { c: set() for c in namskeid }

    for s in M.nemendur:
      ekki_sami_stadur[s] = { c: set() for c in namskeid }
    for i, netfang in enumerate(ekki_sami_stadur_df['netfang']):
      nams = set(clean_split(ekki_sami_stadur_df['námskeið'][i], ';'))

      if netfang not in M.nemendur:
        raise Exception(f'Nemandinn {netfang} í ekki_sami_stadur í {auka_upplysingar} fannst ekki í nemendaskráningu í {skraningar} skjalinu.')
      for c in nams:
        if c not in M.klinik:
          raise Exception(f'Námskeiðið {c} úr ekki_sami_stadur í {auka_upplysingar} fannst ekki í {mrs} skjalinu.')

      if len(nams) == 0:
        nams = namskeid

      stadir = set(clean_split(ekki_sami_stadur_df['staður'][i], ';'))
      for c in nams:
        for st in stadir:
          if st not in klinik_stadir[c] and st not in failed_stadir[c]:
            failed_stadir[c].add(st)
            warnings.append(f'Staðurinn {st} í ekki_sami_stadur í {auka_upplysingar} fannst ekki í {mrs} skjalinu fyrir námskeiðið {c}.')
        ekki_sami_stadur[netfang][c] = stadir

  except KeyError as kerr:
    raise Exception(f'Rangt netfang/námskeið gefið í {auka_upplysingar}/ekki_sami_stadur: {kerr}')

  M.ekki_sami_stadur = ekki_sami_stadur
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Vikur per hólf

  stundatafla_klinik = stundatafla_df[stundatafla_df['klíník byrjar í viku'] != '']
  try:
    stundatafla_klinik = stundatafla_klinik.astype({ 'klíník byrjar í viku': int })
  except ValueError as err:
    raise Exception(f'Gildi í "klíník byrjar í viku" dálki í stundatöflu {skraningar} ekki heiltala: {err}')

  klinik_vikur = dict()
  for c in set(stundatafla_klinik['námskeið']):
    temp = dict()
    for i in stundatafla_klinik[stundatafla_klinik['námskeið'] == c].index:
      v = stundatafla_klinik.loc[i, 'vika']
      q = stundatafla_klinik.loc[i, 'klíník byrjar í viku']
      n = stundatafla_klinik.loc[i, 'fjöldi vikna']
      temp.update({ v + q - 1: set(range(v, v + n)) })
    klinik_vikur.update({ c: temp })

  M.klinik_vikur = klinik_vikur
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Nemendur sem þurfa að klára alla klíník snemma

  klara_snemma = dict()
  try:
    for i, netfang in enumerate(klara_snemma_df['netfang']):
      if netfang not in M.nemendur:
        raise Exception(f'Nemandinn {netfang} í klara_snemma í {auka_upplysingar} fannst ekki í nemendaskráningu í {skraningar} skjalinu.')

      klara_snemma[netfang] = klara_snemma_df['vika'][i]
  except KeyError as kerr:
    raise Exception(f'Vantar dálkinn {kerr} í klara_snemma í {auka_upplysingar} skjalinu.')

  M.klara_snemma = klara_snemma
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Nemendur sem þurfa að klára tiltekna klíník snemma

  klara_snemma_serstakt = dict()
  try:
    for i, netfang in enumerate(klara_snemma_serstakt_df['netfang']):
      nam = klara_snemma_serstakt_df['námskeið'][i]

      if netfang not in M.nemendur:
        raise Exception(f'Nemandinn {netfang} í klara_snemma_serstakt í {auka_upplysingar} fannst ekki í nemendaskráningu í {skraningar} skjalinu.')
      if nam not in M.klinik:
        raise Exception(f'Námskeiðið {nam} í klara_snemma_serstakt í {auka_upplysingar} fannst ekki í {mrs} skjalinu.')

      if netfang not in klara_snemma_serstakt:
        klara_snemma_serstakt[netfang] = dict()
      if nam in klara_snemma_serstakt[netfang]:
        raise Exception(f'Nemandinn {netfang} er tvískráður í klara_snemma_serstakt í {auka_upplysingar} með námskeiðið {nam}.')
      klara_snemma_serstakt[netfang][nam] = klara_snemma_serstakt_df['vika'][i]

  except KeyError as kerr:
    raise Exception(f'Vantar dálkinn {kerr} í klara_snemma_serstakt í {auka_upplysingar} skjalinu.')

  M.klara_snemma_serstakt = klara_snemma_serstakt
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Skrá nemendur á sömu deild

  sama_deild = dict()
  try:
    for s in M.nemendur:
      sama_deild[s] = { c: set() for c in namskeid }
    for i, netfang in enumerate(sama_deild_df['netfang']):
      nam = sama_deild_df['námskeið'][i]

      if netfang not in M.nemendur:
        raise Exception(f'Nemandinn {netfang} í sama_deild í {auka_upplysingar} fannst ekki í nemendaskráningu í {skraningar} skjalinu.')
      if nam not in M.klinik:
        raise Exception(f'Námskeiðið {nam} í sama_deild í {auka_upplysingar} fannst ekki í {mrs} skjalinu.')

      for deild in clean_split(sama_deild_df['deild'][i], ';'):
        if deild not in klinik_deildir[nam]:
          warnings.append(f'Deildin {deild} í sama_deild í {auka_upplysingar} fannst ekki í {mrs} skjalinu fyrir námskeiðið {nam}.')

        sama_deild[netfang][nam].add(deild)

  except KeyError as kerr:
    raise Exception(f'Vantar dálkinn {kerr} í sama_deild í {auka_upplysingar} skjalinu.')

  M.sama_deild = sama_deild
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Skrá nemendur á aðra deild

  ekki_sama_deild = dict()
  try:
    for s in M.nemendur:
      ekki_sama_deild[s] = { c: set() for c in namskeid }
    for i, netfang in enumerate(ekki_sama_deild_df['netfang']):
      nam = ekki_sama_deild_df['námskeið'][i]

      if netfang not in M.nemendur:
        raise Exception(f'Nemandinn {netfang} í ekki_sama_deild í {auka_upplysingar} fannst ekki í nemendaskráningu í {skraningar} skjalinu.')
      if nam not in M.klinik:
        raise Exception(f'Námskeiðið {nam} úr ekki_sama_deild í {auka_upplysingar} fannst ekki í {mrs} skjalinu.')

      for deild in clean_split(ekki_sama_deild_df['deild'][i], ';'):
        if deild not in klinik_deildir[nam]:
          warnings.append(f'Deildin {deild} í ekki_sama_deild í {auka_upplysingar} fannst ekki í {mrs} skjalinu fyrir námskeiðið {nam}.')

        ekki_sama_deild[netfang][nam].add(deild)

  except KeyError as kerr:
    raise Exception(f'Vantar dálkinn {kerr} í ekki_sama_deild í {auka_upplysingar} skjalinu.')

  M.ekki_sama_deild = ekki_sama_deild
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Laga heiti.....

  """
  try:
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
  """
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Óskir um frívikur

  fri_osk = dict()
  try:
    for i, netfang in enumerate(fri_osk_df['netfang']):
      if netfang not in M.nemendur:
        raise Exception(f'Nemandinn {netfang} í fri_osk í {auka_upplysingar} fannst ekki í nemendaskráningu í {skraningar} skjalinu.')

      if netfang in fri_osk:
        fri_osk[netfang] |= set([int(i) for i in clean_split(fri_osk_df['vikur'][i], ';')])
      else:
        fri_osk[netfang] = set([int(i) for i in clean_split(fri_osk_df['vikur'][i], ';')])

  except:
    print('Engin ósk um frí')

  M.fri_osk = fri_osk
  #----------------------------------------------------------------------------

  #----------------------------------------------------------------------------
  # Skilyrtar frívikur

  fri_skilyrt = dict()
  try:
    for i, netfang in enumerate(fri_skilyrt_df['netfang']):
      if netfang not in M.nemendur:
        raise Exception(f'Nemandinn {netfang} í fri_skilyrt í {auka_upplysingar} fannst ekki í nemendaskráningu í {skraningar} skjalinu.')

      if netfang in fri_skilyrt:
        fri_skilyrt[netfang] |= set([int(i) for i in clean_split(fri_skilyrt_df['vikur'][i], ';')])
      else:
        fri_skilyrt[netfang] = set([int(i) for i in clean_split(fri_skilyrt_df['vikur'][i], ';')])

  except:
    print('Ekkert skilyrt frí')

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

  #----------------------------------------------------------------------------
  # Röðun sem er ákveðin fyrirfram

  akvedin_rodun = dict()

  for i, netfang in enumerate(akvedin_rodun_df['netfang']):
    if netfang not in M.nemendur:
      raise Exception(f'Nemandinn {netfang} í akvedin_rodun í {auka_upplysingar} fannst ekki í nemendaskráningu í {skraningar} skjalinu.')

    namskeid = akvedin_rodun_df.loc[i, 'námskeið']

    if akvedin_rodun_df.loc[i,'vika'] == '':
      vikur = set(klinik_vikur[namskeid]) # ef engar vikur eru tilgreindar má skráningin vera í hvaða viku námskeiðsins sem tiltekin deild er möguleg

      if akvedin_rodun_df.loc[i, 'deild'] == '':
        continue # ef bæði mengin eru tóm, þá þarf ekki að bæta við auka skorðu

    else:
      vikur = {int(n) for n in clean_split(akvedin_rodun_df.loc[i,'vika'], ';')}

    deildir = set(clean_split(akvedin_rodun_df.loc[i,'deild'], ';'))
    for d in deildir:
      if d not in klinik_deildir[namskeid]:
        warnings.append(f'Deild {d} í akvedin_rodun í {auka_upplysingar} fannst ekki í {mrs} skjalinu fyrir námskeiðið {namskeid}.')

    if netfang not in akvedin_rodun:
      akvedin_rodun.update({ netfang: dict() })
    akvedin_rodun[netfang].update({ namskeid: { 'deildir': deildir, 'vikur': vikur } })

  M.akvedin_rodun = akvedin_rodun

  M.generate_extra_data()
  M.generate_extra_weeks()

  warnings = list(set(warnings))

  return M, warnings