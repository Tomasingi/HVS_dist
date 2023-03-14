import tkinter as tk
import tkinter.scrolledtext as st
import threading
import os
from model import run_model

class ModelThread(threading.Thread):
  def __init__(self, year, path, root, widget):
    super().__init__()
    self.year = year
    self.path = path
    self.root = root
    self.widget = widget

  def run(self):
    parse_result(run(self.year, self.path), self.root, self.widget)

def run_thread(year, path, root, widget):
  t = ModelThread(year, path, root, widget)
  t.start()
  # t.join()

def run(year_string, path):
  yield [['clear']]
  updates = []
  try:
    year = int(year_string)
  except ValueError:
    updates.append(('error', 'Ártal verður að vera heiltala'))

  if not os.path.exists(path):
    updates.append(('error', 'Mappan finnst ekki'))

  if len(updates) > 0:
    yield updates
    return

  files = ['skraningar.xlsx', 'mrs_stadlad.xlsx', 'auka_upplysingar.xlsx']
  failed_files = []
  for f in files:
    if not os.path.exists(os.path.join(path, f)):
      failed_files.append(f)
  if len(failed_files) > 0:
    txt = 'Mappan inniheldur ekki skrár:'
    for f in failed_files:
      txt += f'\n\t{f}'
    updates.append(['error', txt])

  if len(updates) > 0:
    yield updates
    return

  for update in run_model(year, path):
    try:
      yield [update]
    except Exception as e:
      yield [('error', str(e))]

def parse_result(result, root, widget):
  # widget is a scrolled text

  i = 0
  for updates in result:
    for update in updates:
      widget.config(state=tk.NORMAL)

      if update[0] == 'clear':
        widget.delete('1.0', tk.END)
        widget.config(state=tk.DISABLED)
        continue

      last_line = widget.index(tk.END)
      last_line = int(last_line.split('.')[0])
      next_position = f'{last_line-1}.0'

      text = update[1] + '\n'
      if update[0] == 'running':
        text = '\n> ' + text
      else:
        text = '\n' + text
      widget.insert(tk.END, text)
      if update[0] == 'error':
        widget.tag_config(f't{i}', foreground='red')
        widget.tag_add(f't{i}', next_position, tk.END)
      if update[0] == 'warning':
        widget.tag_config(f't{i}', foreground='yellow')
        widget.tag_add(f't{i}', next_position, tk.END)
      if update[0] == 'running':
        widget.tag_config(f't{i}', foreground='white')
        widget.tag_add(f't{i}', next_position, tk.END)
      if update[0] == 'success':
        widget.tag_config(f't{i}', foreground='green')
        widget.tag_add(f't{i}', next_position, tk.END)
      i += 1

      widget.config(state=tk.DISABLED)
    # root.update()

class InputFrame(tk.Frame):
  def __init__(self, master):
    super().__init__(master)
    self.label_1 = tk.Label(self, text='Ár haustannar: ')
    self.label_1.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)

    self.entry_1 = tk.Entry(self, width=20)
    self.entry_1.grid(row=0, column=1, padx=5, pady=5)

    self.label_2 = tk.Label(self, text='Staðsetning möppu: ')
    self.label_2.grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)

    self.entry_2 = tk.Entry(self, width=20)
    self.entry_2.grid(row=1, column=1, padx=5, pady=5)

def main():
  root = tk.Tk()
  root.title('Stundatöfluröðun')

  left_frame = tk.Frame(root, borderwidth=5, relief='groove')
  left_frame.grid(row=0, column=0, sticky=tk.NSEW)

  upper_left = InputFrame(left_frame)
  upper_left.grid(row=0, column=0)

  lower_left = tk.Frame(left_frame)
  lower_left.grid(row=1, column=0)

  button = tk.Button(lower_left, text='Keyra', command=lambda: run_thread(upper_left.entry_1.get(), upper_left.entry_2.get(), root, right_text))
  button.grid(row=0, column=0)

  right_frame = tk.Frame(root, bg='black', borderwidth=5, relief='groove')
  right_frame.grid(row=0, column=1, sticky=tk.NSEW)
  right_frame.grid_rowconfigure(1, weight=1)
  right_frame.grid_columnconfigure(0, weight=1)

  right_title = tk.Label(right_frame, text='Niðurstöður', bg='black', fg='white', font=('Arial', 20))
  right_title.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)

  right_text = st.ScrolledText(right_frame, bg='black', fg='white', wrap=tk.WORD, font=('Arial', 12), cursor='arrow')
  right_text.grid(row=1, column=0, padx=5, pady=5, sticky=tk.NSEW)
  right_text.config(state=tk.DISABLED)

  root.grid_rowconfigure(0, weight=1)
  root.grid_columnconfigure(1, weight=1)

  root.mainloop()

if __name__ == '__main__':
  main()