def indent(text, prefix='\t'):
  """Indent each line of text by prefix."""
  return prefix + text.replace('\n', f'\n{prefix}')

def main():
  # Unit tests
  print(indent('Hello world!\nThis is a test.'))
  print(indent('Hello world!\nThis is a test.', prefix='  '))
  print(indent('Hello world!\nThis is a test.', prefix='💩💩'))

if __name__ == '__main__':
  main()