import os
from innlestur_2 import read_data
from model_generator import generate_model
from excel_generator import generate_excel
from solution_check import check_solution
from strings import indent

def run_model(year, path):
  # Read the data
  yield ('running', 'Les inn gögn...')
  try:
    M, warnings = read_data(path)
    if len(warnings) > 0:
      yield ('warning', 'Aðvörun:' + indent('\n'.join(warnings), '\n'))
  except Exception as e:
    message = 'Villa kom upp við innlestur gagna:\n' + indent(str(e))
    yield ('error', message)
    return

  # Generate and run the model
  yield ('running', 'Keyri líkan...')
  likan, x, mx, deild_min, deild_max = generate_model(M)
  likan.optimize()

  # Generate the excel files
  yield ('running', 'Bý til Excel skrár...')
  out_path = os.path.join(path, 'out')
  i = 0
  while os.path.exists(out_path):
    # Make sure we don't overwrite an existing folder
    out_path = os.path.join(path, f'out_{i}')
    i += 1
  os.mkdir(out_path)
  generate_excel(M, x, year, out_path)

  # Check the solution
  yield ('running', 'Athuga lausn...')
  warnings = check_solution(x, M)
  # TODO: Print the solution check to the GUI
  if warnings == []:
    yield ('success', 'Engar alvarlegar villur')
  else:
    yield ('warning', 'Aðvörun:\n' + '\n'.join(warnings))

  yield ('success', 'Keyrslu lokið')