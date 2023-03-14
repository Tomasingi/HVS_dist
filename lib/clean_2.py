from pandas import read_excel

def clean(x, lower=True):
  if isinstance(x, dict):
    for i in x:
      cleaner(x[i], lower)
  else:
    cleaner(x, lower)

# Hreinsar dataframe
def cleaner(df, lower=True):
  df.columns = df.columns.str.strip()
  if lower:
    df.columns = df.columns.str.lower()
  df.fillna('', inplace=True)

  for i in df.index:
    for j in df.columns:
      if isinstance(df.loc[i, j], str):
        df.loc[i,j] = df.loc[i,j].replace('\xa0', ' ').strip()
        df.loc[i,j] = df.loc[i,j].lower()

# Skiptir og hreinsar lista
def clean_split(s, delim=';'):
  s = str(s).replace('\xa0', ' ').strip()
  return [x.strip() for x in s.split(delim) if x.strip() != '']

# Les inn og hreinsar Excel skjal
def read_clean_excel(path, sheet_name=0, lower=True):
  try:
    with open(path, 'rb') as f:
      df = read_excel(f, sheet_name)
    clean(df, lower)
    return df
  except FileNotFoundError as err:
    raise Exception(f'Villa: Skráin {path} fannst ekki.')

def main():
  print(clean_split(';', ';'))
  print(clean_split('', ';'))
  print(clean_split('Eitthvað, hér', ';'))
  print(clean_split(' A  ; B          ;;  ;C;'))

if __name__ == '__main__':
  main()