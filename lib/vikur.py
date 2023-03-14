class Vikur:
  def __init__(self):
    self.mid = 25
    self.sym = dict()
    for v in range(self.mid, 53):
      self.sym[v] = v - self.mid
    for v in range(1, self.mid):
      self.sym[v] = v + 52 - self.mid

    self.raun = { self.sym[v]: v for v in self.sym }