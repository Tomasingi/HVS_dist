from vikur import Vikur

def solutionCheck(x, M):
    # TODO: Fjarlægja allar vitnanir í landsbyggð
    # TODO: Athuga allt á skipulagðan hátt
    # TODO: fri_osk

    V = Vikur()
    result = dict()
    # Skráningar í auka vikur
    vantar_plass = dict()
    for c in M.klinik:
        vantar = sum(
            x[s,c,v,'Vantar pláss'].X for s in M.nemendur for v in M.auka_vikur & set(M.klinik[c])
        )
        tmp = set()
        if vantar > 0:
            for s in M.nemendur:
                if sum(x[s,c,v,'Vantar pláss'].X for v in M.auka_vikur & set(M.klinik[c])) > 0:
                    tmp.add(s)
        vantar_plass.update({ c: {  'Fjöldi plássa sem vantar': vantar,
                                    'Nemendur sem fengu ekki pláss': tmp }})
    result.update({ 'Vantar pláss': vantar_plass })

    # Skoða skráningu á landsbyggð
    landsbyggd_skraning = dict()
    for c in M.klinik:
        fjoldi = len({ s for s in M.sami_stadur if len(M.sami_stadur[s][c]) > 0 })
        heild = sum(
            x[s,c,v,d].X for s in M.sami_stadur for v in M.klinik[c]
            for d in { d for d in M.klinik[c][v] if M.klinik[c][v][d].stadur in M.sami_stadur[s][c] }
        )
        fjoldar = dict()
        if fjoldi > 0:
            fjoldar.update({ 'Fjöldi sem óskuðu eftir landsbyggðarplássi' : fjoldi })
            fjoldar.update({ 'Fjöldi af þeim sem fengu landsbyggðarpláss' : heild })
        nemar = dict()
        if heild < fjoldi:
            for s in M.sami_stadur:
                if len(M.sami_stadur[s][c]) > 0:
                    if sum(
                            x[s,c,v,d].X for v in M.klinik[c]
                            for d in { d for d in M.klinik[c][v] if M.klinik[c][v][d].stadur in M.sami_stadur[s][c] }
                        ) < 1:
                        fekk = ''
                        for v in M.klinik[c]:
                            for d in M.klinik[c][v]:
                                if x[s,c,v,d].X > 0:
                                    fekk = d
                                    break
                        nemar.update({ s: { 'Óskaði eftir': M.sami_stadur[s][c],
                                            'Fékk': fekk } })
        landsbyggd_skraning.update({ c: { 'Fjöldar': fjoldar, 'Nemar': nemar } })
    result.update({ 'Landsbyggð skráning': landsbyggd_skraning })

    # Skoða skráningu á ekki landsbyggð
    ekki_landsbyggd_skraning = dict()
    for c in M.klinik:
        ekki_landsbyggd = { s for s in M.sami_stadur if len(M.sami_stadur[s][c]) == 0 }
        fjoldi = len(ekki_landsbyggd)
        heild = sum(
            x[s,c,v,d].X for s in ekki_landsbyggd for v in M.klinik[c]
            for d in (M.stadir[c] & set(M.klinik[c][v])).difference(M.sami_stadur[s][c])
        )
        fjoldar = dict()
        if len(M.stadir[c]) > 0:
            fjoldar.update({ 'Fjöldi sem óskuðu ekki eftir landsbyggðarplássi' : fjoldi })
            fjoldar.update({ 'Fjöldi af þeim sem fengu landsbyggðarpláss' : heild })
        nemar = dict()
        if heild > 0:
            for s in M.sami_stadur:
                if len(M.sami_stadur[s][c]) == 0:
                    if sum(
                            x[s,c,v,d].X for v in M.klinik[c]
                            for d in M.stadir[c] & set(M.klinik[c][v])
                        ) > 0:
                        fekk = ''
                        for v in M.klinik[c]:
                            for d in M.klinik[c][v]:
                                if x[s,c,v,d].X > 0:
                                    fekk = d
                                    break
                        nemar.update({ s: fekk })
        ekki_landsbyggd_skraning.update({ c: {'Fjöldar': fjoldar, 'Nemar': nemar } })
    result.update({ 'Ekki landsbyggð skráning': ekki_landsbyggd_skraning })

    # gera eitthvað fyrir skilyrtar deildir/ekki deildir?
    # skil hjúkrunarstjórnun eftir í ar4 skjalinu?

    # Athuga þá sem vilja klára snemma
    sidasta_vika = dict()
    sidasta_vika_serstakt = { s: dict() for s in M.nemendur }
    for s in M.nemendur:
        for c in M.klinik:
            for v in M.klinik[c]:
                if v > 0:
                    for d in M.klinik[c][v]:
                        if x[s,c,v,d].X > 0:
                            w = max(M.klinik_vikur[c][v])
                            if s not in sidasta_vika:
                                sidasta_vika[s] = w
                            else:
                                if V.sym[v] > V.sym[sidasta_vika[s]]:
                                    sidasta_vika[s] = w
                            sidasta_vika_serstakt[s][c] = w

    for s in M.nemendur:
        if s not in sidasta_vika:
            sidasta_vika[s] = 0

    snemma = dict()
    for s in M.klara_snemma:
        snemma.update({ s: { 'Ósk': M.klara_snemma[s], 'Síðasta': sidasta_vika[s] } })
    result.update({ 'Klára snemma': snemma })

    snemma_serstakt = dict()
    for s in M.klara_snemma_serstakt:
        for c in M.klara_snemma_serstakt[s]:
            if c in sidasta_vika_serstakt[s]:
                if s in snemma_serstakt:
                    snemma_serstakt[s].update({ c: { 'Ósk': M.klara_snemma_serstakt[s][c], 'Síðasta': sidasta_vika_serstakt[s][c] } })
                else:
                    snemma_serstakt.update({ s: { c: { 'Ósk': M.klara_snemma_serstakt[s][c],
                    'Síðasta': sidasta_vika_serstakt[s][c]} } })

    result.update({ 'Klára snemma sérstakt': snemma_serstakt })

    # Skoða yfirbókun
    yfirbokanir = dict()
    for c in M.klinik:
        printed_course = False
        for v in M.klinik[c]:
            printed_week = False
            for d in M.klinik[c][v]:
                uthlutad = sum(x[s,c,v,d].X for s in M.nemendur)
                plass = M.klinik[c][v][d].plass
                if uthlutad > plass:
                    if not printed_course:
                        yfirbokanir.update({ c: dict() })
                        printed_course = True
                    if not printed_week:
                        yfirbokanir[c].update({ v: dict() })
                        printed_week = True
                    yfirbokanir[c][v].update({ d: { 'Úthlutað': uthlutad, 'Pláss': plass} })

    result.update({ 'Yfirbókanir': yfirbokanir })
    return result

def printSolutionCheck(result, verbose = False):
    V = Vikur()

    for c in result['Vantar pláss']:
        k = result['Vantar pláss'][c]['Fjöldi plássa sem vantar']
        if k > 0 or verbose:
            print(f'{c}: vantar {k} pláss')
            print(f"{result['Vantar pláss'][c]['Nemendur sem fengu ekki pláss']} fengu ekki pláss")

    if len(result['Yfirbókanir']) > 0:
        print('Námskeið\t Vika\t Deild\t Pláss\t Úthlutað')
    elif verbose:
        print('Engar deildir voru yfirbókaðar.')
    for c in result['Yfirbókanir']:
        for v in result['Yfirbókanir'][c]:
            for d in result['Yfirbókanir'][c][v]:
                print(f"{c}\t {v}\t {d}\t {result['Yfirbókanir'][c][v][d]['Pláss']}\t {result['Yfirbókanir'][c][v][d]['Úthlutað']}")

    for c in result['Landsbyggð skráning']:
        if len(result['Landsbyggð skráning'][c]['Fjöldar']) > 0:
            if (result['Landsbyggð skráning'][c]['Fjöldar']['Fjöldi sem óskuðu eftir landsbyggðarplássi'] !=
                result['Landsbyggð skráning'][c]['Fjöldar']['Fjöldi af þeim sem fengu landsbyggðarpláss'] or verbose):
                print(f"Fjöldi sem óskuðu eftir landsbyggðarplássi í {c}: {result['Landsbyggð skráning'][c]['Fjöldar']['Fjöldi sem óskuðu eftir landsbyggðarplássi']}")
                print(f"Fjöldi þeirra sem fengu landsbyggðarpláss: {result['Landsbyggð skráning'][c]['Fjöldar']['Fjöldi af þeim sem fengu landsbyggðarpláss']}")
            for s in result['Landsbyggð skráning'][c]['Nemar']:
                print(f"{s} óskaði eftir plássi á {result['Landsbyggð skráning'][c]['Nemar'][s]['Óskaði eftir']} en fékk {result['Landsbyggð skráning'][c]['Nemar'][s]['Fékk']}")

    for c in result['Ekki landsbyggð skráning']:
        if len(result['Ekki landsbyggð skráning'][c]['Fjöldar']) > 0:
            if result['Ekki landsbyggð skráning'][c]['Fjöldar']['Fjöldi af þeim sem fengu landsbyggðarpláss'] > 0 or verbose:
                print(f"Fjöldi sem óskuðu ekki eftir landsbyggðarplássi í {c}: {result['Ekki landsbyggð skráning'][c]['Fjöldar']['Fjöldi sem óskuðu ekki eftir landsbyggðarplássi']}")
                print(f"Fjöldi þeirra sem fengu landsbyggðarpláss: {result['Ekki landsbyggð skráning'][c]['Fjöldar']['Fjöldi af þeim sem fengu landsbyggðarpláss']}")
            for s in result['Ekki landsbyggð skráning'][c]['Nemar']:
                print(f"{s} óskaði eftir ekki eftir landsbyggðarplássi en fékk {result['Ekki landsbyggð skráning'][c]['Nemar'][s]}")

    date_status = ''
    for s in result['Klára snemma']:
        date_ok = False
        if V.sym[result['Klára snemma'][s]['Ósk']] >= V.sym[result['Klára snemma'][s]['Síðasta']]:
            date_status = ':)'
            date_ok = True
        else:
            date_status = ':('

        if not date_ok or verbose:
            print(f"{s} óskaði eftir að klára fyrir viku {result['Klára snemma'][s]['Ósk']}, en klárar í viku {result['Klára snemma'][s]['Síðasta']} {date_status}")

    for s in result['Klára snemma sérstakt']:
        for c in result['Klára snemma sérstakt'][s]:
            date_ok = False
            if V.sym[result['Klára snemma sérstakt'][s][c]['Ósk']] > V.sym[result['Klára snemma sérstakt'][s][c]['Síðasta']]:
                date_status = ':)'
                date_ok = True
            else:
                date_status = ':('

            if not date_ok or verbose:
                print(f"{s} óskaði eftir að klára {c} fyrir viku {result['Klára snemma sérstakt'][s][c]['Ósk']}, en klárar í viku {result['Klára snemma sérstakt'][s][c]['Síðasta']} {date_status}")


def num_errors(result):
    # Number of errors, excluding insufficient capacity
    V = Vikur()
    total = 0

    for c in result['Landsbyggð skráning']:
        if len(result['Landsbyggð skráning'][c]['Fjöldar']) > 0:
            total += result['Landsbyggð skráning'][c]['Fjöldar']['Fjöldi sem óskuðu eftir landsbyggðarplássi'] - result['Landsbyggð skráning'][c]['Fjöldar']['Fjöldi af þeim sem fengu landsbyggðarpláss']

    for c in result['Ekki landsbyggð skráning']:
        if len(result['Ekki landsbyggð skráning'][c]['Fjöldar']) > 0:
            total += result['Ekki landsbyggð skráning'][c]['Fjöldar']['Fjöldi af þeim sem fengu landsbyggðarpláss']

    for s in result['Klára snemma']:
        if V.sym[result['Klára snemma'][s]['Ósk']] <= V.sym[result['Klára snemma'][s]['Síðasta']]:
            total += 1

    for s in result['Klára snemma sérstakt']:
        for c in result['Klára snemma sérstakt'][s]:
            if V.sym[result['Klára snemma sérstakt'][s][c]['Ósk']] <= V.sym[result['Klára snemma sérstakt'][s][c]['Síðasta']]:
                total += 1

    return total