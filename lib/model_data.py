from dataclasses import dataclass, field
from deild import Deild

@dataclass
class ModelData:
  klinik: dict = field(default_factory=dict)
  nemendaskraning: dict = field(default_factory=dict)
  nemendur: dict = field(default_factory=dict)
  val_listi: set = field(default_factory=set)
  val_nemenda: dict = field(default_factory=dict)
  nemendur_val_vikur: dict = field(default_factory=dict)
  klinik_vikur: dict = field(default_factory=dict)
  val_vikur: dict = field(default_factory=dict)
  vikur: set = field(default_factory=set)
  klara_snemma: dict = field(default_factory=dict)
  klara_snemma_serstakt: dict = field(default_factory=dict)
  sama_deild: dict = field(default_factory=dict)
  ekki_sama_deild: dict = field(default_factory=dict)
  sami_stadur: dict = field(default_factory=dict)
  ekki_sami_stadur: dict = field(default_factory=dict)
  fri_osk: dict = field(default_factory=dict)
  fri_skilyrt: dict = field(default_factory=dict)
  auka_vikur: set = field(default_factory=set)

  stadir: dict = field(default_factory=dict)
  akvedin_rodun: dict = field(default_factory=dict)

  def generate_extra_weeks(self):
    i = 0
    fjoldi = len(self.nemendur)
    for c in self.klinik:
      i -= 1
      self.klinik[c].update({ i: {'Vantar pláss': Deild(heiti='auka', vidfang='00000', plass=fjoldi, stadur='', hofudborgarsvaedi=True, postnumer=101, stjori='', netfang='', simanumer='113')} })

    self.auka_vikur = set(range(i,0))

  def generate_extra_data(self):
    for c in self.klinik:
      self.stadir[c] = set()
    for s in self.sami_stadur:
      for c in self.sami_stadur[s]:
        for d in self.sami_stadur[s][c]:
          self.stadir[c].add(d)