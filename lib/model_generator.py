import gurobipy as gp
from postur import Postur
from vikur import Vikur

def generate_model(M):
  postur = Postur()
  V = Vikur()
  sym_vikur = V.sym

  likan = gp.Model("likan")
  x = likan.addVars([(s,c,v,d) for s in M.nemendur for c in M.klinik for v in M.klinik[c] for d in M.klinik[c][v]], vtype=gp.GRB.BINARY)
  mx = likan.addVars([c for c in M.klinik], vtype=gp.GRB.CONTINUOUS)
  deild_min = likan.addVars([(c,v) for c in M.klinik for v in M.klinik[c]], vtype=gp.GRB.CONTINUOUS)
  deild_max = likan.addVars([(c,v) for c in M.klinik for v in M.klinik[c]], vtype=gp.GRB.CONTINUOUS)

  # vigt_frontload = 10**2
  vigt_rada_jafnt = 10**2
  vigt_postnumer = 10
  vigt_klara_snemma = 10**6
  vigt_klara_snemma_serstakt = 10**6
  vigt_serstakur_stadur = 10**4
  vigt_auka_vikur = 10**7
  vigt_serstakar_deildir = 10**5
  vigt_fri_osk = 10**3

  likan.setObjective(
    # frontloading, fylla frekar fyrstu vikurnar
    # gp.quicksum(
    #   x[s,c,v,d] * sym_vikur[v]
    #   for s in M.nemendur for c in M.klinik for v in set(M.klinik[c]).difference(M.auka_vikur) for d in M.klinik[c][v]
    # ) * vigt_frontload

    # Raða jafnt á deildir sem eru annars eins
    gp.quicksum(
      deild_max[c,v] - deild_min[c,v]
      for c in M.klinik for v in M.klinik[c]
      if v > 0 and len(M.klinik[c][v]) > 0
    ) * vigt_rada_jafnt

    # Raða nemendum á deildir sem eru nálægt heimilum þeirra
    + gp.quicksum(
      x[s,c,v,d] * postur.fjar(M.nemendur[s].postnumer, M.klinik[c][v][d].postnumer)
      for s in M.nemendur
      for c in M.klinik
      for v in M.klinik[c]
      for d in M.klinik[c][v]
    ) * vigt_postnumer

    # Leyfa ákveðnum nemendum að klára klíník snemma, t.d. vegna barnseigna
    + gp.quicksum(
      x[s,c,v,d] for s in M.klara_snemma
      for c in M.klinik
      for v in set(M.klinik[c]).difference(M.auka_vikur)
      if sym_vikur[v] >= sym_vikur[M.klara_snemma[s]] for d in M.klinik[c][v]
    ) * vigt_klara_snemma

    # Leyfa ákveðnum nemendum að klára sérstök námskeið snemma
    + gp.quicksum(
      x[s,c,v,d] for s in M.klara_snemma_serstakt
      for c in M.klara_snemma_serstakt[s]
      for v in set(M.klinik[c]).difference(M.auka_vikur)
      if sym_vikur[v] >= sym_vikur[M.klara_snemma_serstakt[s][c]] for d in M.klinik[c][v]
    ) * vigt_klara_snemma_serstakt

    # Setja nemendur í klíník á ákveðna staði (landsbyggðaskráning t.d.)
    - gp.quicksum(
      x[s,c,v,d] for s in M.nemendur
      for c in M.klinik
      for v in M.klinik[c]
      for d in { d for d in M.klinik[c][v] if M.klinik[c][v][d].stadur in M.sami_stadur[s][c] }
    ) * vigt_serstakur_stadur

    # Ekki setja nemendur á stað sem þeir báðu um að fara ekki á
    + gp.quicksum(
      x[s,c,v,d] for s in M.nemendur
      for c in M.klinik
      for v in M.klinik[c]
      for d in { d for d in M.klinik[c][v] if M.klinik[c][v][d].stadur in M.ekki_sami_stadur[s][c] }
    ) * vigt_serstakur_stadur

    # Ekki setja nemendur á stað sem þeir báðu ekki um að fara á
    + gp.quicksum(
      x[s,c,v,d] for s in M.nemendur
      for c in M.klinik
      for v in M.klinik[c]
      for d in { d for d in M.klinik[c][v] if M.klinik[c][v][d].stadur in M.stadir[c].difference(M.sami_stadur[s][c]) }
    ) * vigt_serstakur_stadur

    # Ekki setja nemendur í auka plássin sem eru búin til svo að módelið geti samt keyrt
    + gp.quicksum(
      x[s,c,v,'Vantar pláss'] for s in M.nemendur
      for c in M.klinik
      for v in M.auka_vikur & set(M.klinik[c])
    ) * vigt_auka_vikur

    # Setja nemendur í ákveðnar deildir
    - gp.quicksum(
      x[s,c,v,d] for s in M.sama_deild
      for c in M.sama_deild[s]
      for d in M.sama_deild[s][c]
      for v in M.vikur if d in M.klinik[c][v]
    ) * vigt_serstakar_deildir

    # Setja nemendur ekki í ákveðnar deildir
    + gp.quicksum(
      x[s,c,v,d] for s in M.ekki_sama_deild
      for c in M.ekki_sama_deild[s]
      for d in M.ekki_sama_deild[s][c]
      for v in M.vikur if d in M.klinik[c][v]
    ) * vigt_serstakar_deildir

    # Gefa nemendum frí í umbeðnum vikum
    + gp.quicksum(
      x[s,c,v,d] for s in M.fri_osk
      for c in M.klinik
      for v in M.klinik[c] if v > 0
      for d in M.klinik[c][v]
      if len(set(M.fri_osk[s]) & set(M.klinik_vikur[c][v])) > 0
    ) * vigt_fri_osk

    + gp.quicksum(
      mx[c] for c in M.klinik
    )
    , gp.GRB.MINIMIZE
  )

  # 1. Allir nemendur fá klíník sem þau eru skráð í
  # (nákvæmlega einu sinni per klíník)
  likan.addConstrs(
    gp.quicksum(
      x[s,c,v,d] for v in M.klinik[c] for d in M.klinik[c][v]
    ) == M.nemendaskraning[s][c]
    for s in M.nemendur
    for c in M.klinik
  )

  # 2. Fjöldi nemenda í klíník er ekki meiri en pláss
  likan.addConstrs(
    gp.quicksum(
      x[s,c,v,d] for s in M.nemendur
    ) <= M.klinik[c][v][d].plass
    for c in M.klinik
    for v in M.klinik[c]
    for d in M.klinik[c][v]
  )

  # 3. Engin skörun á milli klínískra námskeiða
  likan.addConstrs(
    gp.quicksum(
      x[s,c1,v1,d1] for d1 in M.klinik[c1][v1]
    ) <= 1 - gp.quicksum(
      x[s,c2,v2,d2] for d2 in M.klinik[c2][v2]
    ) for s in M.nemendur
    for c1 in M.klinik_vikur if M.nemendaskraning[s][c1] == 1
    for c2 in M.klinik_vikur if M.nemendaskraning[s][c2] == 1
    for v1 in M.klinik_vikur[c1] if v1 > 0
    for v2 in M.klinik_vikur[c2] if v2 > 0
    if (c1 != c2)
    if len(M.klinik_vikur[c1][v1] & M.klinik_vikur[c2][v2]) > 0
  )

  # 4. Engin skörun á milli klínískra námskeiða og valnámskeiða
  likan.addConstrs(
    gp.quicksum(
      x[s,c,v,d] for d in M.klinik[c][v]
    ) == 0
    for s in M.nemendur
    for c in M.klinik_vikur if M.nemendaskraning[s][c] == 1
    for v in M.klinik_vikur[c]
    if len(set(M.klinik_vikur[c][v]) & M.nemendur_val_vikur[s]) > 0
  )

  # 5. Skilyrt frí
  likan.addConstr(
    gp.quicksum(
      x[s,c,v,d] for s in M.fri_skilyrt
      for c in M.klinik
      for v in M.klinik[c] if v > 0
      for d in M.klinik[c][v]
      if len(set(M.fri_skilyrt[s]) & set(M.klinik_vikur[c][v])) > 0
    ) == 0
  )

  # 6. Fyrirfram ákveðnar skráningar
  for s in M.akvedin_rodun:
    for c in M.akvedin_rodun[s]:
      if len(M.akvedin_rodun[s][c]['deildir']) == 0: # ef engar sérstakar deildir voru tilgreindar, förum við bara eftir gefnum vikum
        likan.addConstr(
          gp.quicksum(
            x[s,c,v,d] for v in M.akvedin_rodun[s][c]['vikur'] for d in M.klinik[c][v]
          ) == M.nemendaskraning[s][c]
        )
      else:
        likan.addConstr(
          gp.quicksum(
            x[s,c,v,d] for v in M.akvedin_rodun[s][c]['vikur'] for d in M.akvedin_rodun[s][c]['deildir'] if d in M.klinik[c][v]
          ) == M.nemendaskraning[s][c]
        )

  # Dreifa jafnt á vikur; mjúk skorða
  likan.addConstrs(
    gp.quicksum(
      M.klinik[c][v][d].plass for d in M.klinik[c][v]
    )
    - gp.quicksum(
      x[s,c,v,d] for s in M.nemendur for d in M.klinik[c][v]
    ) >= mx[c]
    for c in M.klinik
    for v in M.klinik[c] if v > 0 and len(M.klinik[c][v]) > 0
  )

  # Dreifa jafnt á deildir; mjúk skorða
  likan.addConstrs(
    gp.quicksum(
      x[s,c,v,d] for s in M.nemendur
    ) <= deild_max[c,v]
    for c in M.klinik
    for v in M.klinik[c] if v > 0 and len(M.klinik[c][v]) > 0
    for d in M.klinik[c][v] if M.klinik[c][v][d].hofudborgarsvaedi and M.klinik[c][v][d].plass > 0
  )

  # frh.
  likan.addConstrs(
    gp.quicksum(
      x[s,c,v,d] for s in M.nemendur
    ) >= deild_min[c,v]
    for c in M.klinik
    for v in M.klinik[c] if v > 0 and len(M.klinik[c][v]) > 0
    for d in M.klinik[c][v] if M.klinik[c][v][d].hofudborgarsvaedi and M.klinik[c][v][d].plass > 0
  )

  return likan, x, mx, deild_min, deild_max