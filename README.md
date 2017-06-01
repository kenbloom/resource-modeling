# resource-modeling
Programs to model future CMS computing resource needs

`cpu.py` is a python program to calculate estimates of future CMS CPU needs and expected availability.  It takes two arguments: first is the annual rate of improvement in CPU, and the second is the annual rate of improvement in software.  These get printed on the plot that is made at the end to help make sure you got them in the right order.

`disk.py` takes parameters from `BaseModel.json`, `EventCounts.json`, and another `[model].json` file as inputs
and determines the disk and tape usage by year.
