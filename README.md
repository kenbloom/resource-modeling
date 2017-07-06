# resource-modeling
Programs to model future CMS computing resource needs

`cpu.py` is a python program to calculate estimates of future CMS CPU needs and expected availability.  

`data.py` is a python program to calculate future disk and tape needs.

`events.py` plots the numbers of events of data, LHC MC, and HL-LHC MC needed per year.

All three programs takes one argument which is a comma separated list of configuration (JSON) files. The parameters contained in `BaseModel.json` and `RealisticModel.json` are used as defaults. Files from the comma separated list are read in order and used to override the default values.
