import os
from model import run_model

def failed_excel_files(path):
  files = ['skraningar.xlsx', 'mrs_stadlad.xlsx', 'auka_upplysingar.xlsx']
  failed = []
  for f in files:
    if not os.path.exists(os.path.join(path, f)):
      failed.append(f)
  return failed

def main():
  prompt = 'Ár: '
  try:
    year = int(input(prompt))
  except ValueError:
    print('Villa: Ártal verður að vera heiltala')
    return

  prompt = 'Staðsetning möppu: '
  path = input(prompt)
  if not os.path.exists(path):
    print('Villa: Mappan finnst ekki')
    return

  failed = failed_excel_files(path)
  if len(failed) > 0:
    print('Villa: Mappan inniheldur ekki skrár:')
    for f in failed:
      print(f'\t{f}')
    return

  run_model(year, path)

if __name__ == '__main__':
  main()